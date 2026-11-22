"""Fetch the single self-contained WASI CPython release and verify its digest."""

import hashlib
from pathlib import Path
import urllib.request

root = Path(__file__).resolve().parents[1]
path = root / ".models/python-3.12.0.wasm"
url = "https://github.com/vmware-labs/webassembly-language-runtimes/releases/download/python%2F3.12.0%2B20231211-040d5a6/python-3.12.0.wasm"
digest = "e5dc5a398b07b54ea8fdb503bf68fb583d533f10ec3f930963e02b9505f7a763"
if __name__ == "__main__":
    path.parent.mkdir(exist_ok=True)
    if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        with urllib.request.urlopen(url, timeout=60) as response:
            data = response.read(27_000_000)
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError("WASI release checksum mismatch")
        temp = path.with_suffix(".partial")
        temp.write_bytes(data)
        temp.replace(path)
    print("Verified", path)
