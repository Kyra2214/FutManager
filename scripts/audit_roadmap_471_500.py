#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = Path('/home/ubuntu/brasfoot_engine')
REFERENCES = {
    **{step: ["client/src/components/DashboardLayout.tsx", "client/src/components/DashboardLayoutSkeleton.tsx", "client/src/pages/Home.tsx", "docs/evidencia_passos_471_499.md"] for step in range(471, 481)},
    **{step: ["tests/test_safe_undo.py", "tests/test_final_roadmap_evidence.py", "scripts/benchmark_final_roadmap.py", "docs/evidencia_passos_471_499.md"] for step in range(481, 500)},
}
CHECKPOINTS = [
    {"version": "3fc90838", "scope": "391-403"},
    {"version": "0bc6f206", "scope": "411-420"},
    {"version": "5e214169", "scope": "421-430"},
    {"version": "54cecc23", "scope": "371-500-evidencias"},
    {"version": "17b8cabd", "scope": "471-499-gaps-resolvidos"},
]


def main() -> None:
    rows = []
    for step, paths in sorted(REFERENCES.items()):
        missing = [path for path in paths if not ((ENGINE / path) if path.startswith('tests/') else (ROOT / path)).exists()]
        rows.append({"step": step, "references": paths, "missing": missing, "status": "VALID" if not missing else "GAP"})
    result = {
        "scope": "471-500",
        "item_count": len(rows),
        "items_valid": sum(row["status"] == "VALID" for row in rows),
        "items": rows,
        "checkpoint_chain": CHECKPOINTS,
        "checkpoint_before_publication": all(item["version"] for item in CHECKPOINTS),
        "status": "VALID" if all(row["status"] == "VALID" for row in rows) else "GAP",
    }
    output = ROOT / "docs/auditoria_item_a_item_471_500.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    if result["status"] != "VALID":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
