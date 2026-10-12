"""Entry point: python -m app.sim  or  make simulate"""
import logging
import os
import sys

os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")

# Suppress stderr noise from MLflow / PowerShell NativeCommandError false-positive
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

from app.sim.runner import run_simulation_study

if __name__ == "__main__":
    result = run_simulation_study()
    sys.exit(0)
