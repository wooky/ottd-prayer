import asyncio
from asyncio.log import logger
import logging
import dacite
import sys
import yaml

from src.config import Config
from src.game_protocol import GameProtocol
from src.prayer_bot import PrayerBot


async def main(filename: str) -> None:
    with open(filename) as f:
        config = dacite.from_dict(data_class=Config, data=yaml.safe_load(f))

    logging.basicConfig(level=config.bot.log_level)

    loop = asyncio.get_running_loop()

    app = PrayerBot(config)
    transport, protocol = await loop.create_connection(lambda: GameProtocol(
        app), config.server.server_host, config.server.server_port)

    await app.set_protocol_and_join(protocol)
    try:
        await protocol.task
    finally:
        transport.close()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage:", sys.argv[0], "[config file]")
        sys.exit(1)

    asyncio.run(main(sys.argv[1]))
