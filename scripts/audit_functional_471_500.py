#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = Path('/home/ubuntu/brasfoot_engine')


def run(name: str, command: list[str], cwd: Path, timeout: int = 240) -> dict:
    started = time.perf_counter()
    completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    output = (completed.stdout + completed.stderr)[-4000:]
    return {"name": name, "command": command, "exit_code": completed.returncode, "elapsed_ms": round((time.perf_counter() - started) * 1000, 2), "output": output, "passed": completed.returncode == 0}


def main() -> None:
    checks = [
        run("python_full_suite", ["python3", "-m", "pytest", "-q"], ENGINE, 300),
        run("vitest_full_suite", ["pnpm", "exec", "vitest", "run"], ROOT, 300),
        run("typescript", ["pnpm", "exec", "tsc", "--noEmit"], ROOT, 180),
        run("production_build", ["pnpm", "run", "build"], ROOT, 240),
        run("safe_undo_and_seasons", ["python3", "-m", "pytest", "-q", "tests/test_safe_undo.py", "tests/test_final_roadmap_evidence.py"], ENGINE, 120),
        run("governance_validators", ["python3", "scripts/validate_shared_gateway_contracts.py"], ROOT, 120),
        run("mutation_path_validator", ["python3", "scripts/validate_mutation_paths.py"], ROOT, 120),
        run("database_validator", ["python3", "scripts/validate_p0_database.py"], ROOT, 120),
        run("bootstrap_benchmark", ["python3", "scripts/benchmark_final_roadmap.py", "/home/ubuntu/brasfoot_engine/data/state/game.db", "docs/benchmark_final_471_499.json"], ROOT, 120),
        run("item_audit", ["python3", "scripts/audit_roadmap_471_500.py"], ROOT, 120),
    ]
    result = {"scope": "471-500", "checks": checks, "passed": sum(item["passed"] for item in checks), "total": len(checks), "status": "VALID" if all(item["passed"] for item in checks) else "GAP"}
    (ROOT / "docs/auditoria_funcional_471_500.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "passed": result["passed"], "total": result["total"]}, ensure_ascii=False))
    if result["status"] != "VALID":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
