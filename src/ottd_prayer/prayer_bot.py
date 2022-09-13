import asyncio
import logging
from hashlib import md5
from typing import Any, Optional, cast

from dacite import from_dict

from .bot_structures import (
    ClientId,
    CompanyId,
    NetworkErrorCode,
    PlayerMovement,
    ServerError,
    ServerFrame,
    ServerProperties,
)
from .config import Config
from .decorators import app_consumer
from .game_protocol import GameProtocol
from .saveload import ChTable, SaveloadBuffer

logger = logging.getLogger(__name__)
MAX_COMPANIES = 0x0F
COMPANY_SPECTATOR = 255
DAY_TICKS = 74


class PrayerBot:
    def __init__(self, config: Config) -> None:
        self.config = config

        self.protocol: GameProtocol
        self.ban_check_task: asyncio.Task[None]
        self.server_properties: ServerProperties
        self.frame_counter: int
        self.target_company_id: Optional[CompanyId] = (
            config.server.company_id - 1
            if config.server.company_id is not None
            else None
        )
        self.company_move_task: Optional[asyncio.Task[None]] = None
        self.was_game_password_sent: bool = False
        self.ready_to_play: bool = False
        self.is_playing: bool = False
        self.other_clients_playing: set[ClientId] = set()
        self.token: int = 0
        self.last_ack_frame: int = 0
        self.should_reconnect: bool = config.bot.auto_reconnect
        self.saveload: Optional[SaveloadBuffer] = None

    async def set_protocol_and_join(self, protocol: GameProtocol) -> None:
        logger.debug("Setting protocol")
        self.protocol = protocol

        try:
            logger.debug("Waiting to confirm the bot didn't get banned")
            self.ban_check_task = asyncio.create_task(asyncio.sleep(1))
            await self.ban_check_task
        except asyncio.CancelledError:
            # bail!
            return

        logger.debug("Joining remote server")
        if (
            self.config.ottd.revision_major == None
            or self.config.ottd.revision_minor == None
        ):
            (revision_major, revision_minor) = map(
                int, self.config.ottd.network_revision.split(".")
            )
        else:
            revision_major = cast(int, self.config.ottd.revision_major)
            revision_minor = cast(int, self.config.ottd.revision_minor)
        newgrf_version = (
            (revision_major + 16) << 24
            | revision_minor << 20
            | int(self.config.ottd.revision_stable) << 19
            | 28004
        )

        await protocol.send_PACKET_CLIENT_JOIN(
            self.config.ottd.network_revision,
            newgrf_version,
            self.config.server.player_name,
            COMPANY_SPECTATOR,
        )

    ### CALLED BY TCPPROTOCOL ###

    @app_consumer(logger)
    async def receive_PACKET_SERVER_FULL(self) -> None:
        logger.warning("Server is full")
        self._reconnect_if(self.config.bot.auto_reconnect)

    @app_consumer(logger)
    async def receive_PACKET_SERVER_BANNED(self) -> None:
        logger.warning("Bot is banned")
        self._reconnect_if(self.config.bot.auto_reconnect_if_banned)

    @app_consumer(logger)
    async def receive_PACKET_SERVER_ERROR(self, **kwargs: dict[str, Any]) -> None:
        server_error = from_dict(data_class=ServerError, data=kwargs)
        if 0 <= server_error.error_code < NetworkErrorCode.NETWORK_ERROR_END:
            error_code_str = str(NetworkErrorCode(server_error.error_code))
        else:
            error_code_str = "INVALID"
        logger.error(
            "Received server error %d (%s): %s",
            server_error.error_code,
            error_code_str,
            server_error.error_str,
        )

        if server_error.error_code == NetworkErrorCode.NETWORK_ERROR_WRONG_PASSWORD:
            logger.error("Incorrect game password")
            self._reconnect_if(self.config.bot.auto_reconnect_if_wrong_game_password)
        else:
            self._reconnect_if(self.config.bot.auto_reconnect)

    @app_consumer(logger)
    async def receive_PACKET_SERVER_CHECK_NEWGRFS(self) -> None:
        await self.protocol.send_PACKET_CLIENT_NEWGRFS_CHECKED()

    @app_consumer(logger)
    async def receive_PACKET_SERVER_NEED_GAME_PASSWORD(self) -> None:
        server_password = self.config.server.server_password
        if server_password == None:
            logger.error("Server password was not set")
            self._reconnect_if(self.config.bot.auto_reconnect_if_wrong_game_password)
            return
        assert (
            server_password is not None
        )  # otherwise mypy complains for whatever reason

        await self.protocol.send_PACKET_CLIENT_GAME_PASSWORD(server_password)

    @app_consumer(logger)
    async def receive_PACKET_SERVER_WELCOME(self, **kwargs: dict[str, Any]) -> None:
        self.server_properties = from_dict(data_class=ServerProperties, data=kwargs)

        await self.protocol.send_PACKET_CLIENT_GETMAP()

    @app_consumer(logger)
    async def receive_PACKET_SERVER_CLIENT_INFO(self, **kwargs: dict[str, Any]) -> None:
        player_movement = from_dict(data_class=PlayerMovement, data=kwargs)

        await self._do_player_movement(
            player_movement.client_id, player_movement.company_id
        )

    @app_consumer(logger)
    async def receive_PACKET_SERVER_WAIT(self) -> None:
        pass

    @app_consumer(logger)
    async def receive_PACKET_SERVER_MAP_BEGIN(self, frame: int) -> None:
        self.frame_counter = frame
        if self.target_company_id is None:
            self.saveload = SaveloadBuffer()

    @app_consumer(logger)
    async def receive_PACKET_SERVER_MAP_SIZE(self) -> None:
        pass

    @app_consumer(logger)
    async def receive_PACKET_SERVER_MAP_DATA(self, map_data: memoryview) -> None:
        if self.saveload is not None:
            logger.debug("Appending %d bytes of map data", len(map_data))
            self.saveload.append(map_data)

    @app_consumer(logger)
    async def receive_PACKET_SERVER_MAP_DONE(self) -> None:
        if self.saveload is not None:
            if self.config.bot.saveload_dump_file:
                with open(self.config.bot.saveload_dump_file, "wb") as f:
                    f.write(self.saveload.to_bytes())
            chunks = self.saveload.decode()
            plyr = chunks["PLYR"]
            assert isinstance(plyr, ChTable)
            company_name = cast(str, self.config.server.company_name).encode("UTF-8")
            target_company_id = next(
                (
                    i
                    for i, v in enumerate(plyr.elements)
                    if "name" in v and v["name"] == company_name
                ),
                None,
            )
            if target_company_id is None:
                logger.error("Cannot find specified company")
                self._reconnect_if(self.config.bot.auto_reconnect_if_company_not_found)
                return
            self.target_company_id = target_company_id
            logger.debug("Setting target company ID to %d", target_company_id + 1)
            self.saveload = None  # no longer needed
        self.ready_to_play = True
        await self.protocol.send_PACKET_CLIENT_MAP_OK()

    @app_consumer(logger)
    async def receive_PACKET_SERVER_JOIN(self) -> None:
        pass

    @app_consumer(logger)
    async def receive_PACKET_SERVER_FRAME(self, **kwargs: dict[str, Any]) -> None:
        server_frame = from_dict(data_class=ServerFrame, data=kwargs)

        if server_frame.token != None:
            assert server_frame.token is not None
            self.token = server_frame.token

        self.frame_counter = max(
            server_frame.frame_counter_server, server_frame.frame_counter_max
        )

        if self.last_ack_frame < self.frame_counter:
            logger.debug("Sending ACK for day")
            self.last_ack_frame = self.frame_counter + DAY_TICKS
            await self.protocol.send_PACKET_CLIENT_ACK(self.frame_counter, self.token)

    @app_consumer(logger)
    async def receive_PACKET_SERVER_SYNC(self) -> None:
        pass

    @app_consumer(logger)
    async def receive_PACKET_SERVER_COMMAND(self) -> None:
        pass

    @app_consumer(logger)
    async def receive_PACKET_SERVER_CHAT(self) -> None:
        pass

    @app_consumer(logger)
    async def receive_PACKET_SERVER_EXTERNAL_CHAT(self) -> None:
        pass

    @app_consumer(logger)
    async def receive_PACKET_SERVER_MOVE(self, **kwargs: dict[str, Any]) -> None:
        player_movement = from_dict(data_class=PlayerMovement, data=kwargs)

        await self._do_player_movement(
            player_movement.client_id, player_movement.company_id
        )

    @app_consumer(logger)
    async def receive_PACKET_SERVER_COMPANY_UPDATE(self) -> None:
        pass

    @app_consumer(logger)
    async def receive_PACKET_SERVER_CONFIG_UPDATE(self) -> None:
        pass

    @app_consumer(logger)
    async def receive_PACKET_SERVER_NEWGAME(self) -> None:
        logger.warning("Server is about to restart")
        self._reconnect_if(self.config.bot.auto_reconnect_if_restarting)

    @app_consumer(logger)
    async def receive_PACKET_SERVER_SHUTDOWN(self) -> None:
        logger.warning("Server is shutting down")
        self._reconnect_if(self.config.bot.auto_reconnect_if_shutdown)

    @app_consumer(logger)
    async def receive_PACKET_SERVER_QUIT(self, client_id: ClientId) -> None:
        assert client_id != self.server_properties.client_id

        await self._do_player_movement(client_id, COMPANY_SPECTATOR)

    @app_consumer(logger)
    async def receive_PACKET_SERVER_ERROR_QUIT(self, client_id: ClientId) -> None:
        assert client_id != self.server_properties.client_id

        await self._do_player_movement(client_id, COMPANY_SPECTATOR)

    ### PRIVATE METHODS ###

    def _reconnect_if(self, condition: bool) -> None:
        self.should_reconnect = condition
        self.ban_check_task.cancel()
        if self.company_move_task is not None:
            self.company_move_task.cancel()
        self.protocol.task.cancel()

    # GenerateCompanyPasswordHash from src/network/network.cpp
    def _company_password_hash(self) -> str:
        password_str = self.config.server.company_password
        if password_str == None:
            return ""
        assert password_str is not None  # otherwise mypy complains for whatever reason

        password = password_str.encode("UTF-8")
        server_id = self.server_properties.server_id.encode("UTF-8")
        game_seed = self.server_properties.game_seed

        salted_password = bytearray()
        for i in range(32):
            password_char = password[i] if i < len(password) else 0
            server_id_char = server_id[i] if i < len(server_id) else 0
            seed_char = game_seed >> (i % 32)
            salted_password_char = (password_char ^ server_id_char ^ seed_char) & 0xFF
            salted_password.append(salted_password_char)

        checksum = md5(bytes(salted_password)).digest()
        return checksum.hex()

    async def _do_player_movement(
        self, client_id: ClientId, company_id: CompanyId
    ) -> None:
        # Set/unset own company ID if the player movement is for us, join anyways
        if client_id == self.server_properties.client_id:
            self.is_playing = company_id == self.target_company_id
            await self._try_joining_company()

        # Track other players playing, play ourselves if we haven't yet
        elif company_id <= MAX_COMPANIES:
            self.other_clients_playing.add(client_id)
            await self._try_joining_company()

        # Track other players leaving/spectating, spectate ourselves if desired
        else:
            self.other_clients_playing.discard(client_id)
            if (
                self.ready_to_play
                and self.is_playing
                and len(self.other_clients_playing) == 0
                and self.config.bot.spectate_if_alone
            ):
                await self.protocol.send_PACKET_CLIENT_MOVE(COMPANY_SPECTATOR, "")

    async def _try_joining_company(self) -> None:
        if self.ready_to_play:
            if self.is_playing:
                # Client was moved, so cancel checking task
                if self.company_move_task is not None:
                    self.company_move_task.cancel()
                    self.company_move_task = None
            elif (self.company_move_task is None or self.company_move_task.done()) and (
                not self.config.bot.spectate_if_alone
                or len(self.other_clients_playing) > 0
            ):
                await self.protocol.send_PACKET_CLIENT_MOVE(
                    cast(int, self.target_company_id), self._company_password_hash()
                )
                self.company_move_task = asyncio.create_task(
                    self._wait_for_move_or_disconnect()
                )

    async def _wait_for_move_or_disconnect(self) -> None:
        logger.debug("Waiting to confirm if the move was successful")
        await asyncio.sleep(1)
        logger.error("Bot was not moved to the requested company")
        self._reconnect_if(self.config.bot.auto_reconnect_if_cannot_move)
