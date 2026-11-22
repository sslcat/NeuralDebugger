import json
import os
import sys

from .facts import checked_prose
from .hybrid import HYBRIDS, Pipeline


def emit(value):
    print(json.dumps(value), flush=True)


def main():
    backend = os.getenv("ND_BACKEND", "base")
    pipeline = Pipeline(backend, os.getenv("ND_ADAPTER"))
    status = {
        "mode": pipeline.mode,
        "device": pipeline.engine.device,
        "warning": pipeline.warning,
    }
    emit(status)
    for line in sys.stdin:
        item = json.loads(line)
        try:
            prediction = pipeline.predict(item["code"], item["traceback"])
            answer = prediction.diagnosis()
            answer, source = checked_prose(item["code"], item["traceback"], answer)
            response = {
                "diagnosis": answer.model_dump(),
                "prose_source": source,
                **status,
            }
            if pipeline.mode in HYBRIDS:
                response["hybrid"] = {
                    "classifier_category": prediction.classifier_label,
                    "conditioned": prediction.conditioned,
                    "fallback": prediction.fallback,
                }
            emit(response)
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
