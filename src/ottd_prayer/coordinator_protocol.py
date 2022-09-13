from openttd_protocol.protocol.coordinator import PacketCoordinatorType
from openttd_protocol.wire.read import read_string, read_uint8, read_uint16
from openttd_protocol.wire.tcp import TCPProtocol
from openttd_protocol.wire.write import write_init, write_string, write_uint8

from .bot_structures import RemoteServer, ServerError
from .decorators import Receive, data_consumer, data_producer

NETWORK_COORDINATOR_VERSION = 6


class CoordinatorProtocol(TCPProtocol):
    PacketType = PacketCoordinatorType
    PACKET_END = PacketCoordinatorType.PACKET_COORDINATOR_END

    ### RECEIVERS ###

    @staticmethod
    @data_consumer
    def receive_PACKET_COORDINATOR_GC_ERROR(data: memoryview) -> Receive:
        error_code, data = read_uint8(data)
        error_str, data = read_string(data)

        return ServerError(error_code=error_code, error_str=error_str).to_dict(), data

    @staticmethod
    @data_consumer
    def receive_PACKET_COORDINATOR_GC_CONNECTING(data: memoryview) -> Receive:
        _, data = read_string(data)  # token
        _, data = read_string(data)  # invite token

        return {}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_COORDINATOR_GC_CONNECT_FAILED(data: memoryview) -> Receive:
        _, data = read_string(data)  # token

        return {}, data

    @staticmethod
    @data_consumer
    def receive_PACKET_COORDINATOR_GC_DIRECT_CONNECT(data: memoryview) -> Receive:
        _, data = read_string(data)  # token
        _, data = read_uint8(data)  # tracking number
        host, data = read_string(data)
        port, data = read_uint16(data)

        return RemoteServer(host=host, port=port).to_dict(), data

    @staticmethod
    @data_consumer
    def receive_PACKET_COORDINATOR_GC_STUN_REQUEST(data: memoryview) -> Receive:
        _, data = read_string(data)  # token

        return {}, data

    ### SENDERS ###

    @data_producer
    def send_PACKET_COORDINATOR_CLIENT_CONNECT(self, invite_code: str) -> bytearray:
        data = write_init(PacketCoordinatorType.PACKET_COORDINATOR_CLIENT_CONNECT)
        write_uint8(data, NETWORK_COORDINATOR_VERSION)
        write_string(data, invite_code)
        return data
