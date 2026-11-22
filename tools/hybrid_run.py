"""Sequential, offline GPU evaluation. Keep only one model-owning process at a time."""
import os
import subprocess
import sys

from neuraldebugger.hybrid_trial import OUT, ARMS
from neuraldebugger.settings import ROOT

def main():
    env=dict(os.environ,ND_DEVICE="cuda",HF_HUB_OFFLINE="1",PYTHONUTF8="1",TRANSFORMERS_VERBOSITY="error")
    exe=sys.executable
    if os.name=="nt" and sys.prefix!=sys.base_prefix:
        exe=sys._base_executable
        env["__PYVENV_LAUNCHER__"]=sys.executable
    for arm in ("hybrid-conditioned","hybrid-display","base","adapter"):
        with (OUT/f"{arm}-gpu.csv").open("x") as log:
            monitor=subprocess.Popen(["nvidia-smi","--query-gpu=timestamp,name,utilization.gpu,memory.used,memory.total",
                "--format=csv,nounits","-l","1"],stdout=log)
            try:
                subprocess.run([exe,"-u","-m","neuraldebugger.hybrid_trial",arm],check=True,cwd=ROOT,env=env,timeout=1800)
            finally:
                monitor.terminate()
                monitor.wait(timeout=10)

if __name__=="__main__":
    main()

