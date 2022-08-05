import logging
from dacite import from_dict
from openttd_protocol.wire.source import Source
from typing import Any, Optional, cast

from .bot_structures import RemoteServer, ServerError
from .config import Config
from .coordinator_protocol import CoordinatorProtocol

logger = logging.getLogger(__name__)


class IpFinder:
    def __init__(self, config: Config) -> None:
        self.config = config

        self.protocol: CoordinatorProtocol
        self.remote_server: Optional[RemoteServer] = None

    async def set_protocol_and_query(self, protocol: CoordinatorProtocol) -> None:
        self.protocol = protocol

        await protocol.send_PACKET_COORDINATOR_CLIENT_CONNECT(cast(str, self.config.server.invite_code))

    ### CALLED BY TCPPROTOCOL ###

    async def receive_PACKET_COORDINATOR_GC_ERROR(self, source: Source, **kwargs: dict[str, Any]) -> None:
        server_error = from_dict(data_class=ServerError, data=kwargs)
        logger.error("Received server error %d: %s",
                     server_error.error_code, server_error.error_str)
        raise Exception("Cannot retrieve server IP")

    async def receive_PACKET_COORDINATOR_GC_CONNECTING(self, source: Source) -> None:
        logger.debug("Received PACKET_COORDINATOR_GC_CONNECTING")

    async def receive_PACKET_COORDINATOR_GC_CONNECT_FAILED(self, source: Source) -> None:
        raise Exception("Cannot retrieve server IP")

    async def receive_PACKET_COORDINATOR_GC_DIRECT_CONNECT(self, source: Source, **kwargs: dict[str, Any]) -> None:
        logger.debug(
            "Received PACKET_COORDINATOR_GC_DIRECT_CONNECT: %s", kwargs)
        self.remote_server = from_dict(data_class=RemoteServer, data=kwargs)

        self.protocol.task.cancel()

    async def receive_PACKET_COORDINATOR_GC_STUN_REQUEST(self, source: Source) -> None:
        logger.error("NOT IMPLEMENTED: cannot make STUN request")
        raise Exception("Cannot retrieve server IP")
