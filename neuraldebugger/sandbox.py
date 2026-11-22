"""Offline benchmark only. No filesystem, sockets, environment or inherited stdio."""
import ast
import hashlib
import threading

from .settings import ROOT

WASM = ROOT / ".models/python-3.12.0.wasm"
DIGEST = "e5dc5a398b07b54ea8fdb503bf68fb583d533f10ec3f930963e02b9505f7a763"

class Sandbox:
    def __init__(self):
        import wasmtime as w
        if hashlib.sha256(WASM.read_bytes()).hexdigest() != DIGEST:
            raise ValueError("Incorrect WASI interpreter digest")
        config = w.Config()
        config.consume_fuel = True
        config.epoch_interruption = True
        self.engine = w.Engine(config)
        self.module = w.Module.from_file(self.engine, str(WASM))
        self.linker = w.Linker(self.engine)
        self.linker.define_wasi()
        if self.run("print(42)") != b"42":
            raise RuntimeError("WASI startup probe failed")

    def run(self, script):
        import wasmtime as w
        out = bytearray()
        def capture(chunk):
            if len(out) + len(chunk) > 8192:
                return 0
            out.extend(chunk)
            return len(chunk)
        with w.Store(self.engine) as store:
            store.set_limits(memory_size=128 * 2**20, instances=1, memories=1)
            store.set_fuel(300_000_000)
            store.set_epoch_deadline(1)
            wasi = w.WasiConfig()
            wasi.argv = ["python", "-I", "-S", "-B", "-c", script]
            wasi.stdout_custom = capture
            store.set_wasi(wasi)
            timer = threading.Timer(3, self.engine.increment_epoch)
            timer.start()
            try:
                entry = self.linker.instantiate(store, self.module).exports(store)["_start"]
                entry(store)
            except w.ExitTrap as exc:
                if exc.code != 0:
                    return None
            except w.Trap:
                return None
            finally:
                timer.cancel()
                timer.join()
        return bytes(out).strip()

    def score(self, code, case):
        passed = 0
        for args, expected in case["checks"]:
            script = f"{code}\nprint(repr({case['function']}(*{args!r})))"
            raw = self.run(script)
            try:
                value = ast.literal_eval(raw.decode("utf-8")) if raw is not None else object()
                passed += isinstance(value, bool) == isinstance(expected, bool) and value == expected
            except (SyntaxError, ValueError, UnicodeError, RecursionError):
                pass
        return passed

