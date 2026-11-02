import threading
import time 

class Cache:
    def __init__(self):
        self.cache = {}
        self.lock = threading.Lock()

    def get_cache(self, name: str, qtype: int):
        with self.lock:
            key = (name.lower(), qtype)
            if key in self.cache:
                record, expiry = self.cache[key]
                if time.time() < expiry:
                    return record
                else:
                    del self.cache[key]

        return None

    def put_cache(self, record):
        with self.lock:
            key = (record.name.lower(), record.type)
            ttl = max(record.ttl, 60)
            expiry = time.time() + ttl
            self.cache[key] = (record, expiry)

    def put_several(self, record: list):
        for r in record:
            self.put_cache(r)

    def clear(self):
         with self.lock:
            self.cache.clear()

    def stats(self) -> dict:
        with self.lock: 
            now = time.time()
            total = len(self.cache)
            valid = sum(1 for _, exp in self.cache.values() if now < exp)
            expired = total - valid
            return {
                "total" : total,
                "valid" : valid,
                "expired" : expired
            }