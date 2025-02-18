from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Union, cast

from dataclass_wizard import YAMLWizard


@dataclass
class Server:
    player_name: str
    server_port: int = 3979
    server_host: Optional[str] = None
    invite_code: Optional[str] = None
    company_id: Optional[int] = None
    company_name: Optional[str] = None
    server_password: Optional[str] = None
    company_password: Optional[str] = None

    def __post_init__(self) -> None:
        if (self.server_host == None) == (self.invite_code == None):
            raise ValueError("Exactly one of [server_host, invite_code] must be set")
        if (self.company_id == None) == (self.company_name == None):
            raise ValueError("Exactly one of [company_id, company_name] must be set")
        if self.company_id != None and not 1 <= self.company_id <= 15:
            raise ValueError("company_id, if set, must be between 1 and 15")
        if not self.player_name.strip():
            raise ValueError("player_name may not be blank")


class AutoReconnectCondition(Enum):
    UNHANDLED = "UNHANDLED"
    CONNECTION_LOST = "CONNECTION_LOST"
    KICKED = "KICKED"
    SERVER_FULL = "SERVER_FULL"
    WRONG_GAME_PASSWORD = "WRONG_GAME_PASSWORD"
    COMPANY_NOT_FOUND = "COMPANY_NOT_FOUND"
    CANNOT_MOVE = "CANNOT_MOVE"
    SERVER_SHUTTING_DOWN = "SERVER_SHUTTING_DOWN"
    BANNED = "BANNED"
    SERVER_RESTARTING = "SERVER_RESTARTING"
    WRONG_REVISION = "WRONG_REVISION"


@dataclass
class Bot:
    spectate_if_alone: bool = True
    auto_reconnect_if: list[AutoReconnectCondition] = field(default_factory=list)
    auto_reconnect: Optional[bool] = None
    auto_reconnect_wait: int = 30
    reconnect_count: int = 3
    log_level: Union[str, int] = "INFO"
    saveload_dump_file: Optional[str] = None

    def __post_init__(self) -> None:
        if self.auto_reconnect_wait <= 0:
            raise ValueError("auto_reconnect_wait must be greater than 0")
        if self.reconnect_count <= 0:
            raise ValueError("reconnect_count must be greater than 0")


@dataclass
class Ottd:
    network_revision: Optional[str] = None
    revision_major: Optional[int] = None
    revision_minor: Optional[int] = None
    revision_stable: bool = True
    coordinator_host: str = "coordinator.openttd.org"
    coordinator_port: int = 3976

    def __post_init__(self) -> None:
        if (self.revision_major == None) != (self.revision_minor == None):
            raise ValueError(
                "revision_major & revision_minor must either both be set or both be unset"
            )


@dataclass
class Config(YAMLWizard):
    server: Server
    bot: Bot
    ottd: Ottd = field(default_factory=Ottd)
