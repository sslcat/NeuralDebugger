import json
import os
import sys

from .model import Engine
from .schema import parse


def emit(value):
    print(json.dumps(value), flush=True)


def main():
    backend = os.getenv("ND_BACKEND", "base")
    if backend not in {"base", "adapter"}:
        raise ValueError("Unknown backend")
    adapter = os.getenv("ND_ADAPTER") if backend == "adapter" else None
    engine = Engine(adapter)
    warning = engine.warning
    if backend == "adapter" and not adapter:
        warning = "Adapter path missing. The base model is active."
    status = {"mode": engine.mode, "device": engine.device, "warning": warning}
    emit(status)
    for line in sys.stdin:
        item = json.loads(line)
        try:
            answer = parse(engine.predict(item["code"], item["traceback"]))
            emit({"diagnosis": answer.model_dump(), **status})
        except OverflowError as exc:
            emit({"error": str(exc), "status": 422})
        except ValueError:
            emit(
                {
                    "error": "The model returned an unusable diagnosis. Try a smaller, self-contained example.",
                    "status": 502,
                }
            )
        except Exception:
            emit({"error": "Local model inference failed.", "status": 503})


if __name__ == "__main__":
    main()
