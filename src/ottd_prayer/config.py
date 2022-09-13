from dataclasses import dataclass
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
            raise ValueError("Only one of [server_host, invite_code] must be set")
        if (self.company_id == None) == (self.company_name == None):
            raise ValueError("Only one of [company_id, company_name] must be set")
        if self.company_id != None and not 1 <= cast(int, self.company_id) <= 15:
            raise ValueError("company_id must be between 1 and 15")


@dataclass
class Bot:
    spectate_if_alone: bool = False
    auto_reconnect: bool = True
    auto_reconnect_wait: int = 30
    reconnect_count: int = 3
    auto_reconnect_if_wrong_game_password: bool = False
    auto_reconnect_if_company_not_found: bool = False
    auto_reconnect_if_cannot_move: bool = False
    auto_reconnect_if_shutdown: bool = False
    auto_reconnect_if_banned: bool = False
    auto_reconnect_if_restarting: bool = False
    log_level: Union[str, int] = "INFO"
    saveload_dump_file: Optional[str] = None

    def __post_init__(self) -> None:
        if self.auto_reconnect_wait <= 0:
            raise ValueError("auto_reconnect_wait must be greater than 0")
        if self.reconnect_count <= 0:
            raise ValueError("reconnect_value must be greater than 0")


@dataclass
class Ottd:
    network_revision: str
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
    ottd: Ottd
