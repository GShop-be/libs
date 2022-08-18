import io
import re
import logging
from functools import partial
from typing import TextIO, Callable, Iterable
from pathlib import Path

import asyncpg
from asyncio import Lock
from alembic.config import Config
from alembic import command
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncConnection

from .exceptions import InitStepFailed

from ..session_maker import SessionMaker

__all__ = [
    'Initializer'
]


class Initializer:
    def __init__(
        self,
        session_maker: SessionMaker,
        metadata: MetaData,
        alembic_config_path: Path,
    ):
        self._engine = session_maker.engine
        self._metadata = metadata
        self._alembic_config_path = alembic_config_path

        self._lock = Lock()

        self._initialization_steps = [
            self._create_db_if_not_exists,
            self._migrate_database_if_needs
        ]

    async def initialize(self) -> None:
        logging.info(f'Run initialization for db [{self._engine.url.database}]')

        for step_index, step_fn in enumerate(self._initialization_steps):
            await self._run_init_step(step_index, step_fn)

    def add_initialization_steps(self, fn: Callable | Iterable[Callable]) -> None:
        if isinstance(fn, Iterable):
            self._initialization_steps.extend(fn)
        else:
            self._initialization_steps.append(fn)

    async def _run_init_step(self, step: int, fn: Callable) -> None:
        step_with_offset = step + 1

        logging.info(f'Run init step [{step_with_offset}], execute [{fn.__name__}]')
        try:
            async with self._lock:
                await fn()
        except Exception:
            logging.exception(f'Init step [{step_with_offset}] was failed by executing [{fn.__name__}]')
            raise InitStepFailed()

    async def _create_db_if_not_exists(self):
        dialect = self._engine.url.get_dialect().name

        database = self._engine.url.database
        user = self._engine.url.username
        password = self._engine.url.password

        try:
            # Т.к. asyncpg не позволяет коннектиться к несуществующей базе, ловим исключение на конекте.
            connection = await asyncpg.connect(database=database, user=user, password=password)
        except asyncpg.InvalidCatalogNameError:
            if dialect == 'postgresql':
                # Конектимся к бд, которая точно существует в инстансах постгреса и оттуда уже создаем новую дб.
                connection = await asyncpg.connect(database='template1', user=user, password=password)
                await connection.execute(f'CREATE DATABASE "{database}" OWNER "{user}"')
            else:
                raise NotImplemented(f'No database creation for dialect [{dialect}]')
        finally:
            await connection.close()

    async def _migrate_database_if_needs(self) -> None:
        buffer = io.StringIO()
        alembic_cfg = self._get_alembic_config(buffer)

        async with self._engine.begin() as connection:
            await connection.run_sync(partial(command.heads, alembic_cfg))
            heads = self._parse_revision(buffer)

            await connection.run_sync(partial(command.current, alembic_cfg))
            current_heads = self._parse_revision(buffer)

            if current_heads != heads:
                await connection.run_sync(self._run_upgrade, alembic_cfg)

    def _get_alembic_config(self, buffer: TextIO) -> Config:
        return Config(str(self._alembic_config_path), stdout=buffer)

    @staticmethod
    def _run_upgrade(connection: AsyncConnection, cfg: Config):
        cfg.attributes['connection'] = connection
        command.upgrade(cfg, "head")

    @staticmethod
    def _parse_revision(buffer: io.StringIO) -> str:
        raw_value = buffer.getvalue()
        search_pattern = re.compile(r"Revision ID: (.*)\n", flags=re.M)
        result = search_pattern.search(raw_value)
        buffer.truncate(0)
        return result.group(1) if result else None
