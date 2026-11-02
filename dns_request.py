from dns_header import Header
from dns_question import Question
from dns_response import Response

class Request:
    def __init__(self, header = None, questions = None,
                 responses = None, authority = None, additional = None):
        self.header = header or Header()
        self.questions = questions or []
        self.responses = responses or []
        self.authority = authority or []
        self.additional = additional or []

    def encode_request(self) -> bytes:
        self.header.qdcount = len(self.questions)
        self.header.ancount = len(self.responses)
        self.header.nscount = len(self.authority)
        self.header.arcount = len(self.additional)

        data = self.header.encode_header()
        names = {}
        offset = 12

        for q in self.questions:
            names[q.qname] = offset
            qdata = q.encode_question()
            data += qdata
            offset += len(qdata)

        for section in [self.responses, self.authority, self.additional]:
            for rec in section: 
                if rec.name not in names:
                    names[rec.name] = offset
                rdata = rec.encode_response(names)
                data += rdata
                offset += len(rdata)

        return data
    
    @staticmethod
    def decode_request(data: bytes) -> 'Request':
        header = Header.decode_header(data)
        offset = 12

        questions = []
        for _ in range(header.qdcount):
            q, offset = Question.decode_question(data, offset)
            questions.append(q)

        responses = []
        for _ in range(header.ancount):
            rec, offset = Response.decode_response(data, offset)
            responses.append(rec)

        authority = []
        for _ in range(header.nscount):
            rec, offset = Response.decode_response(data, offset)
            authority.append(rec) 

        additional = []
        for _ in range(header.arcount):
            rec, offset = Response.decode_response(data, offset)
            additional.append(rec)

        return Request(header, questions, responses, authority, additional)

    def has_response(self, name: str, qtype: int) -> bool:
        return any(r.name.lower() == name.lower() and r.type == qtype
                   for r in self.responses)

    def get_response_ips(self) -> list:
        return [r.rdata for r in self.responses if r.type in (1, 28)]