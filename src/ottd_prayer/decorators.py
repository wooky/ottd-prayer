from typing import Any, Callable, Coroutine, ParamSpec, cast
from openttd_protocol.wire.exceptions import PacketInvalidData
from openttd_protocol.wire.source import Source
from openttd_protocol.wire.tcp import TCPProtocol
from openttd_protocol.wire.write import SEND_TCP_MTU, write_presend


P = ParamSpec('P')
Receive = tuple[dict[str, Any], memoryview]


def data_consumer(func: Callable[[Source, memoryview], Receive]) -> Callable[..., dict[str, Any]]:
    def wrapper_data_consumer(source: Source, data: memoryview) -> dict[str, Any]:
        result, data = func(source, data)
        if len(data) != 0:
            raise PacketInvalidData(
                "more bytes than expected in ", func.__name__, "; remaining: ", len(data))
        return result
    return wrapper_data_consumer


def data_producer(func: Callable[P, bytearray]) -> Callable[P, Coroutine[Any, Any, None]]:
    async def wrapper_data_producer(*args: P.args, **kwargs: P.kwargs) -> None:
        self = cast(TCPProtocol, args[0])
        data = func(*args, **kwargs)
        write_presend(data, SEND_TCP_MTU)
        await self.send_packet(data)
    return wrapper_data_producer
