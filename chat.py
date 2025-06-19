from enum import Enum

class Request_Type(Enum):
    NEW_CONNECTION = b'\x00'
    MESSAGE = b'\x01'
    TRANSFER = b'\x02'
    EXIT = b'\xFF'


class Chat_Request:
    MAX_MESSAGE_SIZE = 1024
    SPLIT_MAGIC = b'\xcc\xdd'

    def __init__(self, packet_type:Request_Type, *args):
        self.type = packet_type
        self.args = args

    def encode(self):
        msg = self.type
        for v in self.args:
            msg += Chat_Packet.SPLIT_MAGIC + str(v).encode()

    def decode(raw_packet):
        message_parts = raw_message.split(SPLIT_MAGIC)
        packet_type = message_parts[0]
        args = message_parts[1:]
        return Chat_Packet(packet_type, *args)
