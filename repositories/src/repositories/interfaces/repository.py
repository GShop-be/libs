from typing import TypeVar, Generic, Collection, Optional

from sqlalchemy.sql.elements import UnaryExpression
from sqlalchemy.sql.expression import BinaryExpression, BooleanClauseList
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import InstrumentedAttribute


T = TypeVar('T')


class BaseRepository(Generic[T]):
    async def find(
        self,
        model: DeclarativeMeta,
        expression: Optional[BinaryExpression | BooleanClauseList] = None,
        order_by: Optional[list[InstrumentedAttribute | UnaryExpression]] = None,
        limit: Optional[int] = None,

    ) -> Collection[T]: ...

    async def find_one(
        self,
        model: DeclarativeMeta,
        expression: Optional[BinaryExpression | BooleanClauseList] = None
    ) -> T: ...

    async def add(self, model: T) -> None: ...

    async def update(self, model: T) -> None: ...

    async def delete(self, model: T) -> None: ...
