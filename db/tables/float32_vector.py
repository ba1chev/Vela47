from array import array
from typing import Optional
from sqlalchemy import LargeBinary
from sqlalchemy import TypeDecorator
from sqlalchemy.engine import Dialect


class Float32Vector(TypeDecorator):
    """An embedding column stored as packed 32-bit floats. A 1024-dimension vector is
    4 KB this way against roughly 20 KB as a JSON list, and reading it back is one copy
    instead of parsing thousands of numbers — which is the whole cost of loading a
    user's documents for a search.

    Float32 is the precision embedding models produce in the first place, so packing
    loses nothing retrieval can notice. The same bytes work on SQLite and PostgreSQL;
    a native vector type such as pgvector would tie DEV and PROD to different code."""

    impl = LargeBinary
    cache_ok = True

    def process_bind_param(self, value: Optional[list[float]], dialect: Dialect) -> Optional[bytes]:
        if value is None:
            return None
        return array("f", value).tobytes()

    def process_result_value(self, value: Optional[bytes], dialect: Dialect) -> Optional[list[float]]:
        if value is None:
            return None
        vector = array("f")
        vector.frombytes(value)
        return vector.tolist()
