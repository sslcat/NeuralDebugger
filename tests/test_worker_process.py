import asyncio

from neuraldebugger.app import Worker
from neuraldebugger.schema import Request


def test_timeout_owns_the_actual_interpreter(monkeypatch):
    # A blocking stand-in advertises its OS PID, then behaves like a stuck generation.
    real_spawn = asyncio.create_subprocess_exec
    spawned = []
    script = (
        "import os,json,sys,time; "
        "print(json.dumps({'mode':'fixture','pid':os.getpid()}),flush=True); "
        "sys.stdin.readline(); time.sleep(60)"
    )

    async def spawn(executable, *args, **kwargs):
        child = await real_spawn(executable, "-u", "-c", script, **kwargs)
        spawned.append(child)
        return child

    async def check():
        service = Worker()
        task = asyncio.create_task(
            service.exchange(Request(code="pass", traceback="fixture"))
        )
        try:
            async with asyncio.timeout(8):
                while "pid" not in service.status:
                    await asyncio.sleep(0.01)
            assert service.status["pid"] == spawned[0].pid
            await service.close()
            assert spawned[0].returncode is not None
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            await service.close()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", spawn)
    asyncio.run(check())
