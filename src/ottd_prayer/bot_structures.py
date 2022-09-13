import enum
from dataclasses import dataclass
from typing import Optional

from dataclass_wizard import JSONSerializable

ClientId = int
CompanyId = int


class NetworkErrorCode(enum.IntEnum):
    NETWORK_ERROR_GENERAL = 0
    NETWORK_ERROR_DESYNC = 1
    NETWORK_ERROR_SAVEGAME_FAILED = 2
    NETWORK_ERROR_CONNECTION_LOST = 3
    NETWORK_ERROR_ILLEGAL_PACKET = 4
    NETWORK_ERROR_NEWGRF_MISMATCH = 5
    NETWORK_ERROR_NOT_AUTHORIZED = 6
    NETWORK_ERROR_NOT_EXPECTED = 7
    NETWORK_ERROR_WRONG_REVISION = 8
    NETWORK_ERROR_NAME_IN_USE = 9
    NETWORK_ERROR_WRONG_PASSWORD = 10
    NETWORK_ERROR_COMPANY_MISMATCH = 11
    NETWORK_ERROR_KICKED = 12
    NETWORK_ERROR_CHEATER = 13
    NETWORK_ERROR_FULL = 14
    NETWORK_ERROR_TOO_MANY_COMMANDS = 15
    NETWORK_ERROR_TIMEOUT_PASSWORD = 16
    NETWORK_ERROR_TIMEOUT_COMPUTER = 17
    NETWORK_ERROR_TIMEOUT_MAP = 18
    NETWORK_ERROR_TIMEOUT_JOIN = 19
    NETWORK_ERROR_INVALID_CLIENT_NAME = 20
    NETWORK_ERROR_END = 21


@dataclass
class ServerError(JSONSerializable):
    error_code: int
    error_str: str


@dataclass
class ServerProperties(JSONSerializable):
    client_id: ClientId
    game_seed: int
    server_id: str


@dataclass
class PlayerMovement(JSONSerializable):
    client_id: ClientId
    company_id: CompanyId


@dataclass
class ServerFrame(JSONSerializable):
    frame_counter_server: int
    frame_counter_max: int
    token: Optional[int]


@dataclass
class RemoteServer(JSONSerializable):
    host: str
    port: int
