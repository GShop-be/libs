from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

__all__ = [
    'SessionMaker'
]


class SessionMaker:
    def __init__(
        self,
        driver: str,
        user: str,
        password: str,
        host: str,
        port: str | int,
        db_name: str,
        echo: bool = False,
        is_async: bool = False
    ):
        engine_maker = create_async_engine if is_async else create_engine

        self._engine = engine_maker(
            f'{driver}://{user}:{password}@{host}:{port}/{db_name}',
            echo=echo,
            future=True
        )

        self._session_maker = sessionmaker(
            self._engine,
            expire_on_commit=False,
            class_=AsyncSession if is_async else Session
        )
        self._session = None

    def __call__(self, *args, **kwargs) -> Session:
        return self._session_maker()

    @property
    def engine(self) -> Engine:
        return self._engine
