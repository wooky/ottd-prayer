import enum
from typing import Any, Callable, Coroutine, ParamSpec, cast
from openttd_protocol.wire.exceptions import PacketInvalidData, PacketTooShort
from openttd_protocol.wire.read import read_uint8, read_uint16, read_uint32, read_uint64, read_string, read_bytes
from openttd_protocol.wire.source import Source
from openttd_protocol.wire.tcp import TCPProtocol
from openttd_protocol.wire.write import write_init, write_presend, write_uint8, write_uint32, write_string, SEND_TCP_MTU
from .bot_structures import PlayerMovement, ServerError, ServerFrame, ServerProperties


class PacketGameType(enum.IntEnum):
    PACKET_SERVER_FULL = 0
    PACKET_SERVER_BANNED = 1
    PACKET_CLIENT_JOIN = 2
    PACKET_SERVER_ERROR = 3
    # PACKET_CLIENT_UNUSED = 4
    # PACKET_SERVER_UNUSED = 5
    # PACKET_SERVER_GAME_INFO = 6
    # PACKET_CLIENT_GAME_INFO = 7
    PACKET_SERVER_CHECK_NEWGRFS = 8
    PACKET_CLIENT_NEWGRFS_CHECKED = 9
    PACKET_SERVER_NEED_GAME_PASSWORD = 10
    PACKET_CLIENT_GAME_PASSWORD = 11
    # PACKET_SERVER_NEED_COMPANY_PASSWORD = 12
    # PACKET_CLIENT_COMPANY_PASSWORD = 13
    PACKET_SERVER_WELCOME = 14
    PACKET_SERVER_CLIENT_INFO = 15
    PACKET_CLIENT_GETMAP = 16
    PACKET_SERVER_WAIT = 17
    PACKET_SERVER_MAP_BEGIN = 18
    PACKET_SERVER_MAP_SIZE = 19
    PACKET_SERVER_MAP_DATA = 20
    PACKET_SERVER_MAP_DONE = 21
    PACKET_CLIENT_MAP_OK = 22
    PACKET_SERVER_JOIN = 23
    PACKET_SERVER_FRAME = 24
    PACKET_CLIENT_ACK = 25
    PACKET_SERVER_SYNC = 26
    # PACKET_CLIENT_COMMAND = 27
    PACKET_SERVER_COMMAND = 28
    # PACKET_CLIENT_CHAT = 29
    PACKET_SERVER_CHAT = 30
    PACKET_SERVER_EXTERNAL_CHAT = 31
    # PACKET_CLIENT_RCON = 32
    # PACKET_SERVER_RCON = 33
    PACKET_CLIENT_MOVE = 34
    PACKET_SERVER_MOVE = 35
    # PACKET_CLIENT_SET_PASSWORD = 36
    # PACKET_CLIENT_SET_NAME = 37
    PACKET_SERVER_COMPANY_UPDATE = 38
    PACKET_SERVER_CONFIG_UPDATE = 39
    PACKET_SERVER_NEWGAME = 40
    PACKET_SERVER_SHUTDOWN = 41
    # PACKET_CLIENT_QUIT = 42
    PACKET_SERVER_QUIT = 43
    # PACKET_CLIENT_ERROR = 44
    PACKET_SERVER_ERROR_QUIT = 45
    PACKET_END = 46


P = ParamSpec('P')
Receive = tuple[dict[str, Any], memoryview]


class GameProtocol(TCPProtocol):
    PacketType = PacketGameType
    PACKET_END = PacketGameType.PACKET_END

    @staticmethod
    def data_consumer(func: Callable[[Source, memoryview], Receive]) -> Callable[..., dict[str, Any]]:
        def wrapper_data_consumer(source: Source, data: memoryview) -> dict[str, Any]:
            result, data = func(source, data)
            if len(data) != 0:
                raise PacketInvalidData(
                    "more bytes than expected in ", func.__name__, "; remaining: ", len(data))
            return result
        return wrapper_data_consumer

    @staticmethod
    def data_producer(func: Callable[P, bytearray]) -> Callable[P, Coroutine[Any, Any, None]]:
        async def wrapper_data_producer(*args: P.args, **kwargs: P.kwargs) -> None:
            self = cast(GameProtocol, args[0])
            data = func(*args, **kwargs)
            write_presend(data, SEND_TCP_MTU)
            await self.send_packet(data)
        return wrapper_data_producer

    ### RECEIVERS ###

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_FULL(source: Source, data: memoryview) -> Receive:
        return {}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_BANNED(source: Source, data: memoryview) -> Receive:
        return {}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_ERROR(source: Source, data: memoryview) -> Receive:
        error_code, data = read_uint8(data)
        try:
            error_str, data = read_string(data)
        except PacketTooShort:
            error_str = "no details provided"

        return ServerError(error_code=error_code, error_str=error_str).__dict__, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_CHECK_NEWGRFS(source: Source, data: memoryview) -> Receive:
        # yeet the data out of the window
        data = memoryview(bytes())

        return {}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_NEED_GAME_PASSWORD(source: Source, data: memoryview) -> Receive:
        return {}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_WELCOME(source: Source, data: memoryview) -> Receive:
        client_id, data = read_uint32(data)
        game_seed, data = read_uint32(data)
        server_id, data = read_string(data)

        return ServerProperties(client_id=client_id, game_seed=game_seed, server_id=server_id).__dict__, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_CLIENT_INFO(source: Source, data: memoryview) -> Receive:
        client_id, data = read_uint32(data)
        playas, data = read_uint8(data)
        _, data = read_string(data)  # name

        return PlayerMovement(client_id=client_id, company_id=playas).__dict__, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_WAIT(source: Source, data: memoryview) -> Receive:
        _, data = read_uint8(data)  # waiting

        return {}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_MAP_BEGIN(source: Source, data: memoryview) -> Receive:
        frame, data = read_uint32(data)

        return {"frame": frame}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_MAP_SIZE(source: Source, data: memoryview) -> Receive:
        _, data = read_uint32(data)  # bytes total

        return {}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_MAP_DATA(source: Source, data: memoryview) -> Receive:
        # yeet the data out of the window
        data = memoryview(bytes())

        return {}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_MAP_DONE(source: Source, data: memoryview) -> Receive:
        return {}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_JOIN(source: Source, data: memoryview) -> Receive:
        _, data = read_uint32(data)  # client ID

        return {}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_FRAME(source: Source, data: memoryview) -> Receive:
        frame_counter_server, data = read_uint32(data)
        frame_counter_max, data = read_uint32(data)
        try:
            token, data = read_uint8(data)
        except PacketTooShort:
            token = None

        return ServerFrame(frame_counter_server=frame_counter_server, frame_counter_max=frame_counter_max, token=token).__dict__, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_SYNC(source: Source, data: memoryview) -> Receive:
        _, data = read_uint32(data)  # sync frame
        _, data = read_uint32(data)  # sync seed 1

        return {}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_COMMAND(source: Source, data: memoryview) -> Receive:
        # yeet the data out of the window
        data = memoryview(bytes())

        return {}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_CHAT(source: Source, data: memoryview) -> Receive:
        _, data = read_uint8(data)  # action
        _, data = read_uint32(data)  # client ID
        _, data = read_bytes(data, 1)  # self send
        _, data = read_string(data)  # messsage
        _, data = read_uint64(data)  # "data"

        return {}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_EXTERNAL_CHAT(source: Source, data: memoryview) -> Receive:
        _, data = read_string(data)  # source
        _, data = read_uint16(data)  # color
        _, data = read_string(data)  # user
        _, data = read_string(data)  # message

        return {}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_MOVE(source: Source, data: memoryview) -> Receive:
        client_id, data = read_uint32(data)  # client ID
        company_id, data = read_uint8(data)  # company ID

        return PlayerMovement(client_id=client_id, company_id=company_id).__dict__, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_COMPANY_UPDATE(source: Source, data: memoryview) -> Receive:
        _, data = read_uint16(data)  # network company passworded???

        return {}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_CONFIG_UPDATE(source: Source, data: memoryview) -> Receive:
        _, data = read_uint8(data)  # max companies
        _, data = read_string(data)  # server name

        return {}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_NEWGAME(source: Source, data: memoryview) -> Receive:
        return {}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_SHUTDOWN(source: Source, data: memoryview) -> Receive:
        return {}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_QUIT(source: Source, data: memoryview) -> Receive:
        client_id, data = read_uint32(data)

        return {"client_id": client_id}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_SERVER_ERROR_QUIT(source: Source, data: memoryview) -> Receive:
        client_id, data = read_uint32(data)
        _, data = read_uint8(data)  # error code

        return {"client_id": client_id}, data

    ### SENDERS ###

    @data_producer
    def send_PACKET_CLIENT_JOIN(self, network_revision: str, newgrf_version: int, client_name: str, playas: int) -> bytearray:
        data = write_init(PacketGameType.PACKET_CLIENT_JOIN)
        write_string(data, network_revision)
        write_uint32(data, newgrf_version)
        write_string(data, client_name)
        write_uint8(data, playas)
        write_uint8(data, 0)  # used to be language
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
    def send_PACKET_CLIENT_MOVE(self, company_id: int, hashed_password: str) -> bytearray:
        data = write_init(PacketGameType.PACKET_CLIENT_MOVE)
        write_uint8(data, company_id)
        write_string(data, hashed_password)
        return data
