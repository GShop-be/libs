from typing import TypeVar
from contextlib import asynccontextmanager

import grpc


T = TypeVar('T')


class GRPCClient:
    def __init__(
        self,
        host: str = 'localhost',
        port: str = '50051'
    ):
        self._host = host
        self._port = port

    @asynccontextmanager
    async def begin(self, stub: T) -> T:
        async with grpc.aio.insecure_channel('localhost:50051') as channel:
            stub = stub(channel)
            yield stub

    def _get_channel_uri(self) -> str:
        return f'{self._host}:{self._port}'
