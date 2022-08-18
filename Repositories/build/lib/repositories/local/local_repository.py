from typing import TypeVar, Collection, Optional, Any

from sqlalchemy import select, update, delete
from sqlalchemy.sql.elements import UnaryExpression
from sqlalchemy.sql.expression import BinaryExpression, BooleanClauseList
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import InstrumentedAttribute

from ..interfaces import BaseRepository


T = TypeVar('T')


class LocalRepository(BaseRepository[T]):

    # TODO: Добавить тип для session_maker.
    def __init__(self, session_maker):
        self._session_maker = session_maker

    async def find(
        self,
        model: DeclarativeMeta,
        expression: Optional[BinaryExpression | BooleanClauseList] = None,
        order_by: Optional[list[InstrumentedAttribute | UnaryExpression]] = None,
        limit: Optional[int] = None,
    ) -> Collection[T]:
        if isinstance(model, (tuple, list)) or isinstance(model, InstrumentedAttribute):
            raise Exception('Нужно предоставить конкретную модель для запрашиваемой сущности.')

        query = select(model)

        if expression is not None:
            query = query.where(expression)

        if order_by is not None:
            query = query.order_by(*order_by)

        if limit is not None:
            query = query.limit(limit)

        return (await self._execute_query(query)).scalars().all()

    async def find_one(
        self,
            model: DeclarativeMeta,
        expression: Optional[BinaryExpression | BooleanClauseList] = None
    ) -> T:
        if isinstance(model, (tuple, list)) or isinstance(model, InstrumentedAttribute):
            raise Exception('Нужно предоставить конкретную модель для запрашиваемой сущности.')

        query = select(model)

        if expression is not None:
            query = query.where(expression)

        return (await self._execute_query(query)).scalars().first()

    async def add(self, model: T) -> None:
        async with self._session_maker() as session:
            async with session.begin():
                session.add(model)

            session.commit()

    async def update(self, model: T) -> None:
        model_class = model.__class__
        primary_key = self._get_primary_key_attribute(model)

        model_fields = self._get_model_fields(model)
        fields_to_update = {key: value for key, value in model_fields if key not in primary_key}

        query = update(model_class).where(
            *[getattr(model_class, key) == getattr(model, key) for key in primary_key]
        ).values(**fields_to_update).execution_options(synchronize_session="fetch")

        await self._execute_query(query, return_=True)

    async def delete(self, model: T) -> None:
        model_class = model.__class__
        primary_key = self._get_primary_key_attribute(model)

        query = delete(model_class).where(
            *[getattr(model_class, key) == getattr(model, key) for key in primary_key]
        ).execution_options(synchronize_session="fetch")

        await self._execute_query(query, return_=True)

    async def _execute_query(self, query, return_: bool = True) -> Any:
        async with self._session_maker() as session:
            result = await session.execute(query)

        return result if return_ else None

    @staticmethod
    def _get_primary_key_attribute(model: T) -> list[InstrumentedAttribute]:
        model_table_name = model.__tablename__

        return [
            column.key
            for column
            in model.metadata.tables[model_table_name].primary_key.columns_autoinc_first
        ]

    @staticmethod
    def _get_model_fields(model: T) -> dict[str, Any]:
        return {key: value for key, value in model.__dict__.values() if not key.startswith('_')}
