import hashlib
from pathlib import Path
from typing import Literal, Union


def hashed(
    value: Union[str, bytes, Path],
    engine: Literal["md5", "sha1", "sha256"] = "md5",
) -> str:
    if engine == "md5":
        hash_engine = hashlib.md5()
    elif engine == "sha1":
        hash_engine = hashlib.sha1()
    elif engine == "sha256":
        hash_engine = hashlib.sha256()
    else:
        raise ValueError(f"hsah engine error: {engine}")

    if isinstance(value, str):
        hash_engine.update(value.encode("utf-8"))
    elif isinstance(value, bytes):
        hash_engine.update(value)
    elif isinstance(value, Path):
        with open(value, "rb") as f:
            while True:
                data = f.read(65535)
                if not data:
                    break
                hash_engine.update(data)
    else:
        raise ValueError(f"type not supported: {type(value)}")
    return hash_engine.hexdigest()
