from dataclasses import dataclass
from enum import IntEnum, auto
from typing import Optional

from dataclass_wizard import JSONSerializable

ClientId = int
CompanyId = int


class NetworkErrorCode(IntEnum):
    NETWORK_ERROR_GENERAL = 0
    NETWORK_ERROR_DESYNC = auto()
    NETWORK_ERROR_SAVEGAME_FAILED = auto()
    NETWORK_ERROR_CONNECTION_LOST = auto()
    NETWORK_ERROR_ILLEGAL_PACKET = auto()
    NETWORK_ERROR_NEWGRF_MISMATCH = auto()
    NETWORK_ERROR_NOT_AUTHORIZED = auto()
    NETWORK_ERROR_NOT_EXPECTED = auto()
    NETWORK_ERROR_WRONG_REVISION = auto()
    NETWORK_ERROR_NAME_IN_USE = auto()
    NETWORK_ERROR_WRONG_PASSWORD = auto()
    NETWORK_ERROR_COMPANY_MISMATCH = auto()
    NETWORK_ERROR_KICKED = auto()
    NETWORK_ERROR_CHEATER = auto()
    NETWORK_ERROR_FULL = auto()
    NETWORK_ERROR_TOO_MANY_COMMANDS = auto()
    NETWORK_ERROR_TIMEOUT_PASSWORD = auto()
    NETWORK_ERROR_TIMEOUT_COMPUTER = auto()
    NETWORK_ERROR_TIMEOUT_MAP = auto()
    NETWORK_ERROR_TIMEOUT_JOIN = auto()
    NETWORK_ERROR_INVALID_CLIENT_NAME = auto()
    NETWORK_ERROR_END = auto()


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
