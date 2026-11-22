import asyncio
import json
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from .schema import Request
from .settings import MODEL, REV, ROOT


class Worker:
    def __init__(self):
        self.process = None
        self.lock = asyncio.Lock()
        self.status = {"mode": "unloaded", "device": None, "warning": None}

    async def close(self):
        if self.process and self.process.returncode is None:
            try:
                self.process.kill()
            except ProcessLookupError:
                pass
            await self.process.wait()
        self.process = None
        self.status = {"mode": "unloaded", "device": None, "warning": None}

    async def exchange(self, item):
        if self.process is not None and self.process.returncode is not None:
            await self.close()
        if self.process is None:
            executable = sys.executable
            env = os.environ.copy()
            if os.name == "nt" and sys.prefix != sys.base_prefix:
                # The venv redirector otherwise spawns a grandchild that survives kill().
                executable = sys._base_executable
                env["__PYVENV_LAUNCHER__"] = sys.executable
            self.process = await asyncio.create_subprocess_exec(
                executable,
                "-u",
                "-m",
                "neuraldebugger.worker",
                cwd=ROOT,
                env=env,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
            )
            self.status = json.loads(await self.process.stdout.readline())
        self.process.stdin.write((item.model_dump_json() + "\n").encode())
        await self.process.stdin.drain()
        return json.loads(await self.process.stdout.readline())

    async def analyze(self, item):
        if self.lock.locked():
            raise HTTPException(
                429,
                "The local model is busy. Retry when the current analysis finishes.",
            )
        async with self.lock:
            try:
                value = await asyncio.wait_for(
                    self.exchange(item), float(os.getenv("ND_TIMEOUT", "150"))
                )
            except asyncio.TimeoutError:
                await self.close()
                raise HTTPException(
                    504, "Analysis timed out. The inference worker was released."
                )
            except asyncio.CancelledError:
                await self.close()
                raise
            except (ValueError, OSError, EOFError):
                await self.close()
                raise HTTPException(
                    503,
                    "The local inference worker could not start or stopped unexpectedly.",
                )
            if "error" in value:
                raise HTTPException(value["status"], value["error"])
            return value


worker = Worker()


@asynccontextmanager
async def lifespan(app):
    yield
    await worker.close()


app = FastAPI(title="NeuralDebugger", lifespan=lifespan)


@app.get("/api/status")
async def status():
    return {
        "model": MODEL,
        "revision": REV,
        "configured": os.getenv("ND_BACKEND", "base"),
        **worker.status,
    }


@app.post("/api/analyze")
async def analyze(item: Request):
    return await worker.analyze(item)


app.mount("/", StaticFiles(directory=ROOT / "web", html=True), name="workbench")
