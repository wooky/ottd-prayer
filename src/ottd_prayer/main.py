import asyncio
import logging
import dacite
import sys
import yaml

from src.bot_structures import RemoteServer
from src.client_runner import run_client
from src.config import Config
from src.coordinator_protocol import CoordinatorProtocol
from src.game_protocol import GameProtocol
from src.ip_finder import IpFinder
from src.prayer_bot import PrayerBot


async def main(filename: str) -> None:
    with open(filename) as f:
        config = dacite.from_dict(data_class=Config, data=yaml.safe_load(f))

    logging.basicConfig(level=config.bot.log_level)

    loop = asyncio.get_running_loop()

    if config.server.server_host is not None:
        remote_server = RemoteServer(
            config.server.server_host, config.server.server_port)
    else:
        ip_finder = await run_client(
            loop,
            RemoteServer(config.ottd.coordinator_host,
                         config.ottd.coordinator_port),
            IpFinder(config),
            CoordinatorProtocol,
            IpFinder.set_protocol_and_query
        )
        if ip_finder.remote_server is None:
            raise Exception("Remote server was not set")
        remote_server = ip_finder.remote_server

    await run_client(
        loop,
        remote_server,
        PrayerBot(config),
        GameProtocol,
        PrayerBot.set_protocol_and_join
    )

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage:", sys.argv[0], "[config file]")
        sys.exit(1)

    asyncio.run(main(sys.argv[1]))
