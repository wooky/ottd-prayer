from dataclasses import dataclass
from typing import Optional

ClientId = int
CompanyId = int


@dataclass
class ServerError:
    error_code: int
    error_str: str


@dataclass
class ServerProperties:
    client_id: ClientId
    game_seed: int
    server_id: str


@dataclass
class PlayerMovement:
    client_id: ClientId
    company_id: CompanyId

@dataclass
class ServerFrame:
    frame_counter_server: int
    frame_counter_max: int
    token: Optional[int]
