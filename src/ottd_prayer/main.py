import asyncio
import logging
import sys
from typing import cast

from .bot_structures import RemoteServer
from .client_runner import run_client
from .config import Config
from .coordinator_protocol import CoordinatorProtocol
from .ip_finder import IpFinder
from .server_connector import connect_to_server


async def main_async(filename: str) -> None:
    if not sys.warnoptions:
        import warnings

        warnings.simplefilter("default")

    config = cast(Config, Config.from_yaml_file(filename))

    logging.basicConfig(level=config.bot.log_level)

    loop = asyncio.get_running_loop()

    if config.server.server_host is not None:
        remote_server = RemoteServer(
            config.server.server_host, config.server.server_port
        )
    else:
        ip_finder = await run_client(
            loop,
            RemoteServer(config.ottd.coordinator_host, config.ottd.coordinator_port),
            IpFinder(config),
            CoordinatorProtocol,
            IpFinder.set_protocol_and_query,
        )
        if ip_finder.remote_server is None:
            raise Exception("Remote server was not set")
        remote_server = ip_finder.remote_server

    await connect_to_server(config, loop, remote_server)


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage:", sys.argv[0], "[config file]")
        sys.exit(1)

    asyncio.run(main_async(sys.argv[1]))
