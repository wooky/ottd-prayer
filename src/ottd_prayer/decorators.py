import logging
from functools import wraps
from typing import Any, Callable, Concatenate, Coroutine, ParamSpec, TypeVar, cast

from openttd_protocol.wire.exceptions import PacketInvalidData
from openttd_protocol.wire.source import Source
from openttd_protocol.wire.tcp import TCPProtocol
from openttd_protocol.wire.write import SEND_TCP_MTU, write_presend

T = TypeVar("T")
P = ParamSpec("P")
Receive = tuple[dict[str, Any], memoryview]


def data_consumer(
    func: Callable[[memoryview], Receive],
) -> Callable[..., dict[str, Any]]:
    def wrapper_data_consumer(source: Source, data: memoryview) -> dict[str, Any]:
        result, data = func(data)
        if len(data) != 0:
            raise PacketInvalidData(
                "more bytes than expected in ",
                func.__name__,
                "; remaining: ",
                len(data),
            )
        return result

    return wrapper_data_consumer


def data_producer(
    func: Callable[P, bytearray],
) -> Callable[P, Coroutine[Any, Any, None]]:
    async def wrapper_data_producer(*args: P.args, **kwargs: P.kwargs) -> None:
        self = cast(TCPProtocol, args[0])
        data = func(*args, **kwargs)
        write_presend(data, SEND_TCP_MTU)
        await self.send_packet(data)

    return wrapper_data_producer


def app_consumer(
    logger: logging.Logger,
) -> Callable[..., Callable[..., Coroutine[Any, Any, None]]]:
    def decorator(
        func: Callable[Concatenate[T, P], Coroutine[Any, Any, None]],
    ) -> Callable[P, Coroutine[Any, Any, None]]:
        @wraps(func)
        async def wrapper_app_consumer(*args: P.args, **kwargs: P.kwargs) -> None:
            logger.debug("%s: %s", func.__name__, kwargs)
            self = cast(T, args[0])
            await func(self, **kwargs) # type: ignore[call-arg]

        return wrapper_app_consumer

    return decorator
