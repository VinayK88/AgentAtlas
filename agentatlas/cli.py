import json
from agentatlas.service import build_report


def main() -> None:
    print(json.dumps(build_report(), indent=2))

if __name__ == "__main__":
    main()
