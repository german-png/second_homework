import struct
import socket
from dns_question import encode_path, decode_path

class Response:
    def __init__(self, name, type, rclass, ttl, rdata):
        self.name = name
        self.type = type
        self.rclass = rclass
        self.ttl = ttl
        self.rdata = rdata

    def encode_response(self, name_with_offset: dict = None):
        encoded_response = b""

        if name_with_offset and self.name in name_with_offset:
            offset = 0xC000 | name_with_offset[self.name]
            encoded_response += struct.pack("!H", offset)
        else:
            encoded_response += encode_path(self.name)

        rdata_bytes = self.encode_rdata()
        encoded_response += struct.pack("!HHIH", self.type, self.rclass,
                                        self.ttl, len(rdata_bytes))

        encoded_response += rdata_bytes
        return encoded_response

    def encode_rdata(self):
        if self.type == 1: # "A"
            return socket.inet_aton(self.rdata)
        elif self.type in [2, 5]: # "NS" или "CNAME"
            return encode_path(self.rdata) 
        elif self.type == 28: # "AAAA"
            return socket.inet_pton(socket.AF_INET6, self.rdata)
        elif isinstance(self.rdata, bytes):
            return self.rdata
        else:
            return str(self.rdata).encode('ascii')

    @staticmethod
    def decode_response(message: bytes, offset: int):
        name, offset = decode_path(message, offset) 

        type, rclass, ttl, rdlength = struct.unpack("!HHIH", message[offset: offset+10])
        offset+=10

        rdata_array = message[offset: offset+rdlength]

        if type == 1 and rdlength == 4:
            rdata = socket.inet_ntoa(rdata_array)
        elif type == 28 and rdlength == 16:
            rdata = socket.inet_ntop(socket.AF_INET6, rdata_array)
        elif type in [2,5] :
            rdata, _ = decode_path(message, offset)
        else: 
            rdata = rdata_array

        return Response(name, type, rclass, ttl, rdata), offset + rdlength

        

        