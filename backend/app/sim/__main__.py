"""Entry point: python -m app.sim  or  make simulate"""
import logging
import os

os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

from app.sim.runner import run_simulation_study

if __name__ == "__main__":
    run_simulation_study()
