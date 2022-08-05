import logging
from typing import Any, Optional, cast
from dacite import from_dict
from hashlib import md5
from openttd_protocol.wire.source import Source

from .game_protocol import GameProtocol
from .bot_structures import ClientId, CompanyId, PlayerMovement, ServerError, ServerFrame, ServerProperties
from .config import Config

logger = logging.getLogger(__name__)
MAX_COMPANIES = 0x0F
COMPANY_SPECTATOR = 255
DAY_TICKS = 74


class PrayerBot:
    def __init__(self, config: Config) -> None:
        self.config = config

        self.protocol: GameProtocol
        self.server_properties: ServerProperties
        self.frame_counter: int
        self.target_company_id: CompanyId = config.server.company_id - 1  # TODO
        self.was_game_password_sent: bool = False
        self.was_company_password_sent: bool = False
        self.ready_to_play: bool = False
        self.is_playing: bool = False
        self.other_clients_playing: set[ClientId] = set()
        self.token: int = 0
        self.last_ack_frame: int = 0
        self.should_reconnect: bool = config.bot.auto_reconnect

    async def set_protocol_and_join(self, protocol: GameProtocol) -> None:
        logger.debug("Setting protocol and joining")
        self.protocol = protocol

        if self.config.ottd.revision_major == None or self.config.ottd.revision_minor == None:
            (revision_major, revision_minor) = map(
                int, self.config.ottd.network_revision.split('.'))
        else:
            revision_major = cast(int, self.config.ottd.revision_major)
            revision_minor = cast(int, self.config.ottd.revision_minor)
        newgrf_version = (revision_major + 16) << 24 | revision_minor << 20 | int(
            self.config.ottd.revision_stable) << 19 | 28004

        await protocol.send_PACKET_CLIENT_JOIN(self.config.ottd.network_revision, newgrf_version, self.config.server.player_name, COMPANY_SPECTATOR)

    ### CALLED BY TCPPROTOCOL ###

    async def receive_PACKET_SERVER_FULL(self, source: Source) -> None:
        logger.warning("Server is full")
        self._reconnect_if(self.config.bot.auto_reconnect)

    async def receive_PACKET_SERVER_BANNED(self, source: Source) -> None:
        logger.warning("Bot is banned")
        self._reconnect_if(self.config.bot.auto_reconnect_if_banned)

    async def receive_PACKET_SERVER_ERROR(self, source: Source, **kwargs: dict[str, Any]) -> None:
        server_error = from_dict(data_class=ServerError, data=kwargs)
        logger.error("Received server error %d: %s",
                     server_error.error_code, server_error.error_str)
        self._reconnect_if(self.config.bot.auto_reconnect)

    async def receive_PACKET_SERVER_CHECK_NEWGRFS(self, source: Source) -> None:
        logger.debug("Received PACKET_SERVER_CHECK_NEWGRFS")
        await self.protocol.send_PACKET_CLIENT_NEWGRFS_CHECKED()

    async def receive_PACKET_SERVER_NEED_GAME_PASSWORD(self, source: Source) -> None:
        logger.debug("Received PACKET_SERVER_NEED_GAME_PASSWORD")
        if self.was_game_password_sent:
            raise RuntimeError("Incorrect game password")

        server_password = self.config.server.server_password
        if server_password == None:
            raise RuntimeError("Server password was not set")
        assert server_password is not None  # otherwise mypy complains for whatever reason

        await self.protocol.send_PACKET_CLIENT_GAME_PASSWORD(server_password)

    async def receive_PACKET_SERVER_WELCOME(self, source: Source, **kwargs: dict[str, Any]) -> None:
        logger.debug("Received PACKET_SERVER_WELCOME: %s", kwargs)
        self.server_properties = from_dict(
            data_class=ServerProperties, data=kwargs)

        await self.protocol.send_PACKET_CLIENT_GETMAP()

    async def receive_PACKET_SERVER_CLIENT_INFO(self, source: Source, **kwargs: dict[str, Any]) -> None:
        logger.debug("Received PACKET_SERVER_CLIENT_INFO: %s", kwargs)
        player_movement = from_dict(data_class=PlayerMovement, data=kwargs)

        await self._do_player_movement(player_movement.client_id, player_movement.company_id)

    async def receive_PACKET_SERVER_WAIT(self, source: Source) -> None:
        logger.debug("Received PACKET_SERVER_WAIT")

    async def receive_PACKET_SERVER_MAP_BEGIN(self, source: Source, frame: int) -> None:
        logger.debug("Received PACKET_SERVER_MAP_BEGIN")
        self.frame_counter = frame

    async def receive_PACKET_SERVER_MAP_SIZE(self, source: Source) -> None:
        logger.debug("Received PACKET_SERVER_MAP_SIZE")

    async def receive_PACKET_SERVER_MAP_DATA(self, source: Source) -> None:
        logger.debug("Received PACKET_SERVER_MAP_DATA")

    async def receive_PACKET_SERVER_MAP_DONE(self, source: Source) -> None:
        logger.debug("Received PACKET_SERVER_MAP_DONE")
        self.ready_to_play = True
        await self.protocol.send_PACKET_CLIENT_MAP_OK()
        # await self._try_joining_company()

    async def receive_PACKET_SERVER_JOIN(self, source: Source) -> None:
        logger.debug("Received PACKET_SERVER_JOIN")

    async def receive_PACKET_SERVER_FRAME(self, source: Source, **kwargs: dict[str, Any]) -> None:
        logger.debug("Received PACKET_SERVER_FRAME: %s", kwargs)
        server_frame = from_dict(data_class=ServerFrame, data=kwargs)

        if server_frame.token != None:
            assert server_frame.token is not None
            self.token = server_frame.token

        self.frame_counter = max(
            server_frame.frame_counter_server, server_frame.frame_counter_max)

        if self.last_ack_frame < self.frame_counter:
            logger.debug("Sending ACK for day")
            self.last_ack_frame = self.frame_counter + DAY_TICKS
            await self.protocol.send_PACKET_CLIENT_ACK(self.frame_counter, self.token)

    async def receive_PACKET_SERVER_SYNC(self, source: Source) -> None:
        logger.debug("Received PACKET_SERVER_SYNC")

    async def receive_PACKET_SERVER_COMMAND(self, source: Source) -> None:
        logger.debug("Received PACKET_SERVER_COMMAND")

    async def receive_PACKET_SERVER_CHAT(self, source: Source) -> None:
        logger.debug("Received PACKET_SERVER_CHAT")

    async def receive_PACKET_SERVER_EXTERNAL_CHAT(self, source: Source) -> None:
        logger.debug("Received PACKET_SERVER_EXTERNAL_CHAT")

    async def receive_PACKET_SERVER_MOVE(self, source: Source, **kwargs: dict[str, Any]) -> None:
        logger.debug("Received PACKET_SERVER_MOVE")
        player_movement = from_dict(data_class=PlayerMovement, data=kwargs)

        await self._do_player_movement(player_movement.client_id, player_movement.company_id)

    async def receive_PACKET_SERVER_COMPANY_UPDATE(self, source: Source) -> None:
        logger.warning("Company password has been changed")

    async def receive_PACKET_SERVER_CONFIG_UPDATE(self, source: Source) -> None:
        logger.debug("Received PACKET_SERVER_CONFIG_UPDATE")

    async def receive_PACKET_SERVER_NEWGAME(self, source: Source) -> None:
        logger.warning("Server is about to restart")
        self._reconnect_if(self.config.bot.auto_reconnect_if_restarting)

    async def receive_PACKET_SERVER_SHUTDOWN(self, source: Source) -> None:
        logger.warning("Server is shutting down")
        self._reconnect_if(self.config.bot.auto_reconnect_if_shutdown)

    async def receive_PACKET_SERVER_QUIT(self, source: Source, client_id: ClientId) -> None:
        logger.debug("Received PACKET_SERVER_QUIT")
        assert client_id != self.server_properties.client_id

        await self._do_player_movement(client_id, COMPANY_SPECTATOR)

    async def receive_PACKET_SERVER_ERROR_QUIT(self, source: Source, client_id: ClientId) -> None:
        logger.debug("Received PACKET_SERVER_ERROR_QUIT")
        assert client_id != self.server_properties.client_id

        await self._do_player_movement(client_id, COMPANY_SPECTATOR)

    ### PRIVATE METHODS ###

    def _reconnect_if(self, condition: bool) -> None:
        self.should_reconnect = condition
        self.protocol.task.cancel()

    # GenerateCompanyPasswordHash from src/network/network.cpp
    def _company_password_hash(self) -> str:
        password_str = self.config.server.company_password
        if password_str == None:
            return ""
        assert password_str is not None  # otherwise mypy complains for whatever reason

        password = password_str.encode('UTF-8')
        server_id = self.server_properties.server_id.encode('UTF-8')
        game_seed = self.server_properties.game_seed

        salted_password = bytearray()
        for i in range(32):
            password_char = password[i] if i < len(password) else 0
            server_id_char = server_id[i] if i < len(server_id) else 0
            seed_char = game_seed >> (i % 32)
            salted_password_char = (
                password_char ^ server_id_char ^ seed_char) & 0xFF
            salted_password.append(salted_password_char)

        checksum = md5(bytes(salted_password)).digest()
        return checksum.hex()

    async def _do_player_movement(self, client_id: ClientId, company_id: CompanyId) -> None:
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
            if self.ready_to_play and self.is_playing and len(self.other_clients_playing) == 0 and self.config.bot.spectate_if_alone:
                await self.protocol.send_PACKET_CLIENT_MOVE(COMPANY_SPECTATOR, "")

    async def _try_joining_company(self) -> None:
        if self.ready_to_play and not self.is_playing and (not self.config.bot.spectate_if_alone or len(self.other_clients_playing) > 0):
            # TODO check if move was successful
            await self.protocol.send_PACKET_CLIENT_MOVE(self.target_company_id, self._company_password_hash())
