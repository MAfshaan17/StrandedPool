import json

from app.services.demo_simulation import run_demo_simulation


if __name__ == "__main__":
    print(json.dumps(run_demo_simulation(), indent=2, default=str))
