from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Union, cast
from warnings import warn

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


class AutoReconnectCondition(Enum):
    NONE = "NONE"
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


@dataclass
class Bot:
    spectate_if_alone: bool = False
    auto_reconnect_if: list[AutoReconnectCondition] = field(default_factory=list)
    auto_reconnect: Optional[bool] = None
    auto_reconnect_wait: int = 30
    reconnect_count: int = 3
    auto_reconnect_if_wrong_game_password: Optional[bool] = None
    auto_reconnect_if_company_not_found: Optional[bool] = None
    auto_reconnect_if_cannot_move: Optional[bool] = None
    auto_reconnect_if_shutdown: Optional[bool] = None
    auto_reconnect_if_banned: Optional[bool] = None
    auto_reconnect_if_restarting: Optional[bool] = None
    log_level: Union[str, int] = "INFO"
    saveload_dump_file: Optional[str] = None

    def __post_init__(self) -> None:
        if self.auto_reconnect_wait <= 0:
            raise ValueError("auto_reconnect_wait must be greater than 0")
        if self.reconnect_count <= 0:
            raise ValueError("reconnect_count must be greater than 0")

        if self.auto_reconnect is not None:
            warn(
                "Setting bot.auto_reconnect is deprecated and will be removed, replaced by bot.auto_reconnect_if with values UNHANDLED, CONNECTION_LOST, KICKED",
                DeprecationWarning,
                stacklevel=2,
            )
            if self.auto_reconnect == True:
                self.auto_reconnect_if.extend(
                    [
                        AutoReconnectCondition.UNHANDLED,
                        AutoReconnectCondition.KICKED,
                        AutoReconnectCondition.CONNECTION_LOST,
                    ]
                )
        if self.auto_reconnect_if_wrong_game_password is not None:
            warn(
                "Setting bot.auto_reconnect_if_wrong_game_password is deprecated and will be removed, replaced by bot.auto_reconnect_if with value WRONG_GAME_PASSWORD",
                DeprecationWarning,
                stacklevel=2,
            )
            if self.auto_reconnect_if_wrong_game_password == True:
                self.auto_reconnect_if.append(
                    AutoReconnectCondition.WRONG_GAME_PASSWORD
                )
        if self.auto_reconnect_if_company_not_found is not None:
            warn(
                "Setting bot.auto_reconnect_if_company_not_found is deprecated and will be removed, replaced by bot.auto_reconnect_if with value COMPANY_NOT_FOUND",
                DeprecationWarning,
                stacklevel=2,
            )
            if self.auto_reconnect_if_company_not_found == True:
                self.auto_reconnect_if.append(AutoReconnectCondition.COMPANY_NOT_FOUND)
        if self.auto_reconnect_if_cannot_move is not None:
            warn(
                "Setting bot.auto_reconnect_if_cannot_move is deprecated and will be removed, replaced by bot.auto_reconnect_if with value CANNOT_MOVE",
                DeprecationWarning,
                stacklevel=2,
            )
            if self.auto_reconnect_if_cannot_move == True:
                self.auto_reconnect_if.append(AutoReconnectCondition.CANNOT_MOVE)
        if self.auto_reconnect_if_shutdown is not None:
            warn(
                "Setting bot.auto_reconnect_if_shutdown is deprecated and will be removed, replaced by bot.auto_reconnect_if with value SERVER_SHUTTING_DOWN",
                DeprecationWarning,
                stacklevel=2,
            )
            if self.auto_reconnect_if_shutdown == True:
                self.auto_reconnect_if.append(
                    AutoReconnectCondition.SERVER_SHUTTING_DOWN
                )
        if self.auto_reconnect_if_banned is not None:
            warn(
                "Setting bot.auto_reconnect_if_banned is deprecated and will be removed, replaced by bot.auto_reconnect_if with value BANNED",
                DeprecationWarning,
                stacklevel=2,
            )
            if self.auto_reconnect_if_banned == True:
                self.auto_reconnect_if.append(AutoReconnectCondition.BANNED)
        if self.auto_reconnect_if_restarting is not None:
            warn(
                "Setting bot.auto_reconnect_if_restarting is deprecated and will be removed, replaced by bot.auto_reconnect_if with value SERVER_RESTARTING",
                DeprecationWarning,
                stacklevel=2,
            )
            if self.auto_reconnect_if_restarting == True:
                self.auto_reconnect_if.append(AutoReconnectCondition.SERVER_RESTARTING)

        if len(self.auto_reconnect_if) == 0:
            raise ValueError(
                "auto_reconnect_if cannot be empty; use special value NONE to never reconnect"
            )


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
