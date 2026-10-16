"""Create ignored local configuration without overwriting user settings."""
import argparse
import json
from pathlib import Path


def initialize(root: Path, name: str | None = None) -> bool:
    root = root.resolve()
    example = root / "config/project.example.json"
    data = json.loads(example.read_text(encoding="utf-8"))
    if name:
        data["project_name"] = name
    target = root / "config/project.local.json"
    created = False
    try:
        # Exclusive creation protects an existing file, including concurrent setup.
        with target.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        created = True
    except FileExistsError:
        pass
    for relative in ("workspace/public", "workspace/private", "workspace/logs"):
        (root / relative).mkdir(parents=True, exist_ok=True)
    return created


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", help="Display name for a newly created local config")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    try:
        created = initialize(root, args.name)
    except (OSError, ValueError) as exc:
        print(f"FAIL: {exc}")
        return 1
    print("Created local config." if created else "Kept existing local config.")
    print("Created ignored workspace folders; no connections or external changes.")
    print("Private grading output still requires a user-approved path outside Git trees.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
