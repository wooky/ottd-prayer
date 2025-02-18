from enum import IntEnum, auto

from openttd_protocol.wire.exceptions import PacketTooShort
from openttd_protocol.wire.read import (
    read_bytes,
    read_string,
    read_uint8,
    read_uint16,
    read_uint32,
    read_uint64,
)
from openttd_protocol.wire.tcp import TCPProtocol
from openttd_protocol.wire.write import (
    write_init,
    write_string,
    write_uint8,
    write_uint32,
)

from .bot_structures import PlayerMovement, ServerError, ServerFrame, ServerProperties
from .decorators import Receive, data_consumer, data_producer


class PacketGameType(IntEnum):
    PACKET_SERVER_FULL = 0
    PACKET_SERVER_BANNED = auto()
    PACKET_CLIENT_JOIN = auto()
    PACKET_SERVER_ERROR = auto()
    PACKET_CLIENT_UNUSED = auto()
    PACKET_SERVER_UNUSED = auto()
    PACKET_SERVER_GAME_INFO = auto()
    PACKET_CLIENT_GAME_INFO = auto()
    PACKET_SERVER_NEWGAME = auto()
    PACKET_SERVER_SHUTDOWN = auto()
    PACKET_SERVER_CHECK_NEWGRFS = auto()
    PACKET_CLIENT_NEWGRFS_CHECKED = auto()
    PACKET_SERVER_NEED_GAME_PASSWORD = auto()
    PACKET_CLIENT_GAME_PASSWORD = auto()
    PACKET_SERVER_NEED_COMPANY_PASSWORD = auto()
    PACKET_CLIENT_COMPANY_PASSWORD = auto()
    PACKET_SERVER_WELCOME = auto()
    PACKET_SERVER_CLIENT_INFO = auto()
    PACKET_CLIENT_GETMAP = auto()
    PACKET_SERVER_WAIT = auto()
    PACKET_SERVER_MAP_BEGIN = auto()
    PACKET_SERVER_MAP_SIZE = auto()
    PACKET_SERVER_MAP_DATA = auto()
    PACKET_SERVER_MAP_DONE = auto()
    PACKET_CLIENT_MAP_OK = auto()
    PACKET_SERVER_JOIN = auto()
    PACKET_SERVER_FRAME = auto()
    PACKET_CLIENT_ACK = auto()
    PACKET_SERVER_SYNC = auto()
    PACKET_CLIENT_COMMAND = auto()
    PACKET_SERVER_COMMAND = auto()
    PACKET_CLIENT_CHAT = auto()
    PACKET_SERVER_CHAT = auto()
    PACKET_SERVER_EXTERNAL_CHAT = auto()
    PACKET_CLIENT_RCON = auto()
    PACKET_SERVER_RCON = auto()
    PACKET_CLIENT_MOVE = auto()
    PACKET_SERVER_MOVE = auto()
    PACKET_CLIENT_SET_PASSWORD = auto()
    PACKET_CLIENT_SET_NAME = auto()
    PACKET_SERVER_COMPANY_UPDATE = auto()
    PACKET_SERVER_CONFIG_UPDATE = auto()
    PACKET_CLIENT_QUIT = auto()
    PACKET_SERVER_QUIT = auto()
    PACKET_CLIENT_ERROR = auto()
    PACKET_SERVER_ERROR_QUIT = auto()
    PACKET_END = auto()


class GameProtocol(TCPProtocol):
    PacketType = PacketGameType
    PACKET_END = PacketGameType.PACKET_END

    ### RECEIVERS ###

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_FULL(data: memoryview) -> Receive:
        return {}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_BANNED(data: memoryview) -> Receive:
        return {}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_ERROR(data: memoryview) -> Receive:
        error_code, data = read_uint8(data)
        try:
            error_str, data = read_string(data)
        except PacketTooShort:
            error_str = "no details provided"

        return ServerError(error_code=error_code, error_str=error_str).to_dict(), data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_GAME_INFO(data: memoryview) -> Receive:
        network_game_info_version, data = read_uint8(data)
        if network_game_info_version > 7:
            raise Exception("Unhandled game info version ", network_game_info_version)
        if network_game_info_version < 1:
            raise Exception(
                "Game info version must be at least 1, got ", network_game_info_version
            )

        # From OpenTTD's SerializeNetworkGameInfo
        if network_game_info_version >= 7:
            _, data = read_uint64(data)
        if network_game_info_version >= 6:
            _, data = read_uint8(data)
        if network_game_info_version >= 5:
            _, data = read_uint32(data)
            _, data = read_string(data)
        if network_game_info_version >= 4:
            grf_count, data = read_uint8(data)
            for i in range(grf_count):
                _, data = read_string(data)
        if network_game_info_version >= 3:
            _, data = read_uint32(data)
            _, data = read_uint32(data)
        if network_game_info_version >= 2:
            _, data = read_uint8(data)
            _, data = read_uint8(data)
            _, data = read_uint8(data)
        # 1
        _, data = read_string(data)
        server_revision, data = read_string(data)
        _, data = read_uint8(data)
        _, data = read_uint8(data)
        _, data = read_uint8(data)
        _, data = read_uint8(data)
        _, data = read_uint16(data)
        _, data = read_uint16(data)
        _, data = read_uint8(data)
        _, data = read_uint8(data)

        return {"server_revision": server_revision}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_CHECK_NEWGRFS(data: memoryview) -> Receive:
        # yeet the data out of the window
        data = memoryview(bytes())

        return {}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_NEED_GAME_PASSWORD(data: memoryview) -> Receive:
        return {}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_WELCOME(data: memoryview) -> Receive:
        client_id, data = read_uint32(data)
        game_seed, data = read_uint32(data)
        server_id, data = read_string(data)

        return (
            ServerProperties(
                client_id=client_id, game_seed=game_seed, server_id=server_id
            ).to_dict(),
            data,
        )

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_CLIENT_INFO(data: memoryview) -> Receive:
        client_id, data = read_uint32(data)
        playas, data = read_uint8(data)
        _, data = read_string(data)  # name

        return PlayerMovement(client_id=client_id, company_id=playas).to_dict(), data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_WAIT(data: memoryview) -> Receive:
        _, data = read_uint8(data)  # waiting

        return {}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_MAP_BEGIN(data: memoryview) -> Receive:
        frame, data = read_uint32(data)

        return {"frame": frame}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_MAP_SIZE(data: memoryview) -> Receive:
        _, data = read_uint32(data)  # bytes total

        return {}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_MAP_DATA(data: memoryview) -> Receive:
        map_data = data
        data = memoryview(bytes())

        return {"map_data": map_data}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_MAP_DONE(data: memoryview) -> Receive:
        return {}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_JOIN(data: memoryview) -> Receive:
        _, data = read_uint32(data)  # client ID

        return {}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_FRAME(data: memoryview) -> Receive:
        frame_counter_server, data = read_uint32(data)
        frame_counter_max, data = read_uint32(data)
        try:
            token, data = read_uint8(data)
        except PacketTooShort:
            token = None

        return (
            ServerFrame(
                frame_counter_server=frame_counter_server,
                frame_counter_max=frame_counter_max,
                token=token,
            ).to_dict(),
            data,
        )

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_SYNC(data: memoryview) -> Receive:
        _, data = read_uint32(data)  # sync frame
        _, data = read_uint32(data)  # sync seed 1

        return {}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_COMMAND(data: memoryview) -> Receive:
        # yeet the data out of the window
        data = memoryview(bytes())

        return {}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_CHAT(data: memoryview) -> Receive:
        _, data = read_uint8(data)  # action
        _, data = read_uint32(data)  # client ID
        _, data = read_bytes(data, 1)  # self send
        _, data = read_string(data)  # messsage
        _, data = read_uint64(data)  # "data"

        return {}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_EXTERNAL_CHAT(data: memoryview) -> Receive:
        _, data = read_string(data)  # source
        _, data = read_uint16(data)  # color
        _, data = read_string(data)  # user
        _, data = read_string(data)  # message

        return {}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_MOVE(data: memoryview) -> Receive:
        client_id, data = read_uint32(data)  # client ID
        company_id, data = read_uint8(data)  # company ID

        return (
            PlayerMovement(client_id=client_id, company_id=company_id).to_dict(),
            data,
        )

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_COMPANY_UPDATE(data: memoryview) -> Receive:
        _, data = read_uint16(data)  # network company passworded
        # This is a bitmask of companies which have a password set.

        return {}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_CONFIG_UPDATE(data: memoryview) -> Receive:
        _, data = read_uint8(data)  # max companies
        _, data = read_string(data)  # server name

        return {}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_NEWGAME(data: memoryview) -> Receive:
        return {}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_SHUTDOWN(data: memoryview) -> Receive:
        return {}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_QUIT(data: memoryview) -> Receive:
        client_id, data = read_uint32(data)

        return {"client_id": client_id}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_ERROR_QUIT(data: memoryview) -> Receive:
        client_id, data = read_uint32(data)
        _, data = read_uint8(data)  # error code

        return {"client_id": client_id}, data

    ### SENDERS ###

    @data_producer
    def send_PACKET_CLIENT_JOIN(
        self, network_revision: str, newgrf_version: int, client_name: str, playas: int
    ) -> bytearray:
        data = write_init(PacketGameType.PACKET_CLIENT_JOIN)
        write_string(data, network_revision)
        write_uint32(data, newgrf_version)
        write_string(data, client_name)
        write_uint8(data, playas)
        write_uint8(data, 0)  # used to be language
        return data

    @data_producer
    def send_PACKET_CLIENT_GAME_INFO(self) -> bytearray:
        data = write_init(PacketGameType.PACKET_CLIENT_GAME_INFO)
        return data

    @data_producer
    def send_PACKET_CLIENT_NEWGRFS_CHECKED(self) -> bytearray:
        data = write_init(PacketGameType.PACKET_CLIENT_NEWGRFS_CHECKED)
        return data

    @data_producer
    def send_PACKET_CLIENT_GAME_PASSWORD(self, password: str) -> bytearray:
        data = write_init(PacketGameType.PACKET_CLIENT_GAME_PASSWORD)
        write_string(data, password)
        return data

    @data_producer
    def send_PACKET_CLIENT_GETMAP(self) -> bytearray:
        data = write_init(PacketGameType.PACKET_CLIENT_GETMAP)
        return data

    @data_producer
    def send_PACKET_CLIENT_MAP_OK(self) -> bytearray:
        data = write_init(PacketGameType.PACKET_CLIENT_MAP_OK)
        return data

    @data_producer
    def send_PACKET_CLIENT_ACK(self, frame_counter: int, token: int) -> bytearray:
        data = write_init(PacketGameType.PACKET_CLIENT_ACK)
        write_uint32(data, frame_counter)
        write_uint8(data, token)
        return data

    @data_producer
    def send_PACKET_CLIENT_MOVE(
        self, company_id: int, hashed_password: str
    ) -> bytearray:
        data = write_init(PacketGameType.PACKET_CLIENT_MOVE)
        write_uint8(data, company_id)
        write_string(data, hashed_password)
        return data
