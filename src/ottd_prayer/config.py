from dataclasses import dataclass
from typing import Optional, Union, cast


@dataclass
class Server:
    server_host: Optional[str]
    invite_code: Optional[str]
    player_name: str
    company_id: Optional[int]
    company_name: Optional[str]
    server_port: int
    server_password: Optional[str]
    company_password: Optional[str]

    def __post_init__(self) -> None:
        if (self.server_host == None) == (self.invite_code == None):
            raise ValueError("Only one of [server_host, invite_code] must be set")
        if (self.company_id == None) == (self.company_name == None):
            raise ValueError("Only one of [company_id, company_name] must be set")
        if self.company_id != None and not 1 <= cast(int, self.company_id) <= 15:
            raise ValueError("company_id must be between 1 and 15")


@dataclass
class Bot:
    spectate_if_alone: bool
    auto_reconnect: bool
    auto_reconnect_wait: int
    reconnect_count: int
    auto_reconnect_if_wrong_game_password: bool
    auto_reconnect_if_company_not_found: bool
    auto_reconnect_if_cannot_move: bool
    auto_reconnect_if_shutdown: bool
    auto_reconnect_if_banned: bool
    auto_reconnect_if_restarting: bool
    log_level: Union[str, int]
    saveload_dump_file: Optional[str]

    def __post_init__(self) -> None:
        if self.auto_reconnect_wait <= 0:
            raise ValueError("auto_reconnect_wait must be greater than 0")
        if self.reconnect_count <= 0:
            raise ValueError("reconnect_value must be greater than 0")


@dataclass
class Ottd:
    network_revision: str
    revision_major: Optional[int]
    revision_minor: Optional[int]
    revision_stable: bool
    coordinator_host: str
    coordinator_port: int

    def __post_init__(self) -> None:
        if (self.revision_major == None) != (self.revision_minor == None):
            raise ValueError(
                "revision_major & revision_minor must either both be set or both be unset"
            )


@dataclass
class Config:
    server: Server
    bot: Bot
    ottd: Ottd
