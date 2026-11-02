import struct

def encode_path(path: str) -> bytes:
    if path.endswith('.'):
        path = path[:-1]
    parts = path.split('.')
    result_path = b''
    for part in parts:
        encoded_part = part.encode('ascii')
        result_path += struct.pack('B', len(encoded_part)) + encoded_part
    result_path += b'\x00'
    return result_path

def decode_path(message : bytes, offset) -> tuple:
    flags = []
    start_offset = offset
    went_to_point = False
    step_cnt = 0

    while True:
        if offset >= len(message):
            break
        length = message[offset]

        if length == 0:
            offset += 1
            break

        if (length & 0xC0) == 0xC0:
            if offset + 1 >= len(message):
                break
            pointer = struct.unpack("!H", message[offset:offset + 2])[0] & 0x3FFF
            if not went_to_point:
                start_offset = offset + 2
            offset = pointer
            went_to_point = True
            step_cnt += 1
            if step_cnt > 20:
                raise ValueError
            continue

        offset += 1
        if offset + length > len(message):
            raise ValueError

        flag = message[offset:offset + length].decode('ascii', errors='replace')
        flags.append(flag)
        offset += length

    if not went_to_point:
        start_offset = offset

    return '.'.join(flags), start_offset

class Question:
    def __init__(self, qname=0, qtype=0, qclass=1):
        self.qname=qname
        self.qtype=qtype
        self.qclass=qclass

    def encode_question(self):
        return encode_path(self.qname) + struct.pack("!HH", self.qtype, self.qclass)

    @staticmethod
    def decode_question(message, offset):
        qname, offset = decode_path(message, offset)
        qtype, qclass = struct.unpack("!HH", message[offset: offset+4])
        return Question(qname, qtype, qclass), offset + 4