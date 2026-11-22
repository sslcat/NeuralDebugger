"""Validation sensitivity control. Never infer from or alter held-out routes here."""
from dataclasses import asdict
import json
from neuraldebugger.corpus import read_rows
from neuraldebugger.hybrid import repair_messages
from neuraldebugger.hybrid_trial import OUT,engine,write
from neuraldebugger.sandbox import Sandbox
from neuraldebugger.trial import score

def main():
    pipeline=engine("hybrid-conditioned")
    box=Sandbox()
    results=[]
    for row in read_rows("validation")[::4]:
        wrong="IndexError" if row["category"]=="WrongResult" else "WrongResult"
        with pipeline.engine.model.disable_adapter():
            raw=pipeline.generate_chat(repair_messages(row["buggy_code"],row["traceback"],wrong))
        results.append(dict(id=row["id"],gold=row["category"],forced_hint=wrong,raw=raw,**score(raw,row,box)))
    write(OUT/"validation/wrong-hint.json",results)

if __name__=="__main__":
    main()

