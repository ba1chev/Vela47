import base64
import struct


def encode_topic_vector(vector: list[float]) -> str:
    return base64.b64encode(struct.pack(f"<{len(vector)}f", *vector)).decode("ascii")


def decode_topic_vector(encoded: str) -> list[float]:
    data = base64.b64decode(encoded)
    return list(struct.unpack(f"<{len(data) // 4}f", data))
