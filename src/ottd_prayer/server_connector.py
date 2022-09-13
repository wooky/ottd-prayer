import asyncio
import logging

from .bot_structures import RemoteServer
from .client_runner import run_client
from .config import AutoReconnectCondition, Config
from .game_protocol import GameProtocol
from .prayer_bot import PrayerBot

logger = logging.getLogger(__name__)


async def connect_to_server(
    config: Config, loop: asyncio.AbstractEventLoop, remote_server: RemoteServer
) -> None:
    while True:
        reconnect_count = 1

        while True:
            try:
                logger.info("Attempt %d to connect to remote server", reconnect_count)
                bot = await run_client(
                    loop,
                    remote_server,
                    PrayerBot(config),
                    GameProtocol,
                    PrayerBot.set_protocol_and_join,
                )
                break
            except ConnectionRefusedError as e:
                logger.error("Cannot connect to remote server: %s", e)

            reconnect_count += 1
            if (
                not AutoReconnectCondition.CONNECTION_LOST
                in config.bot.auto_reconnect_if
                or reconnect_count > config.bot.reconnect_count
            ):
                raise Exception("Connection to remote server lost")

            await _sleep(config)

        if not bot.should_reconnect:
            logger.warning("Not reconnecting any more")
            return

        await _sleep(config)


async def _sleep(config: Config) -> None:
    logger.info(
        "Waiting for %d seconds before retrying", config.bot.auto_reconnect_wait
    )
    await asyncio.sleep(config.bot.auto_reconnect_wait)
