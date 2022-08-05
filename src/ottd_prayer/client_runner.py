from asyncio import AbstractEventLoop, CancelledError
from openttd_protocol.wire.tcp import TCPProtocol
from typing import Any, Callable, Coroutine, TypeVar
from .bot_structures import RemoteServer


App = TypeVar('App')
Protocol = TypeVar('Protocol', bound=TCPProtocol)


async def run_client(
    loop: AbstractEventLoop,
    remote_server: RemoteServer,
    app: App,
    protocol_constructor: Callable[[App], Protocol],
    app_initializer: Callable[[App, Protocol], Coroutine[Any, Any, None]]
) -> App:
    transport, protocol = await loop.create_connection(lambda: protocol_constructor(app), remote_server.host, remote_server.port)

    await app_initializer(app, protocol)
    try:
        await protocol.task
    except CancelledError:
        pass
    finally:
        transport.close()

    return app
