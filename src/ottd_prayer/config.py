from dataclasses import dataclass
import logging
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Server:
    server_host: str
    player_name: str
    company_id: int
    company_name: Optional[str]
    server_port: int
    server_password: Optional[str]
    company_password: Optional[str]

    def __post_init__(self) -> None:
        if not 1 <= self.company_id <= 15:
            raise ValueError("company_id must be between 1 and 15")
        if self.company_name is not None:
            logger.warning("company_name is not implemented")


@dataclass
class Bot:
    spectate_if_alone: bool
    auto_reconnect: bool
    auto_reconnect_wait: int
    reconnect_count: int
    auto_reconnect_if_shutdown: bool
    auto_reconnect_if_banned: bool
    auto_reconnect_if_restarting: bool
    log_level: str

    def __post_init__(self) -> None:
        if self.auto_reconnect_wait <= 0:
            raise ValueError("auto_reconnect_wait must be greater than 0")
        if self.reconnect_count < 0:
            raise ValueError("reconnect_value must be at least 0")


@dataclass
class Ottd:
    network_revision: str
    revision_major: Optional[int]
    revision_minor: Optional[int]
    revision_stable: bool

    def __post_init__(self) -> None:
        if (self.revision_major == None) != (self.revision_minor == None):
            raise ValueError("revision_major & revision_minor must either both be set or both be unset")


@dataclass
class Config:
    server: Server
    bot: Bot
    ottd: Ottd
