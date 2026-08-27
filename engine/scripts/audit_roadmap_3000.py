from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT.parent / "futmanager_frontend" / "docs" / "roadmap_3000_execucao.json"
if not MANIFEST.exists():
    MANIFEST = ROOT.parent / "docs" / "roadmap_3000_execucao.json"
PACKAGE_ROOT = ROOT / "engine" if (ROOT / "engine" / "manager").exists() else ROOT
MODULE_BASE = ROOT.parent if (ROOT / "core").exists() else ROOT
CAREER = PACKAGE_ROOT / "manager" / "career.py"
GATEWAY = ROOT / "scripts" / "career_gateway.py"


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    career = CAREER.read_text(encoding="utf-8")
    gateway = GATEWAY.read_text(encoding="utf-8")
    items = manifest["items"]
    global_source_of_truth = "SQL_GAMESTATE" if "SQL/GameState" in str(manifest.get("policy", "")) else ""
    findings: list[dict[str, object]] = []
    for item in items:
        raw_evidence = item.get("evidence") or {}
        evidence = raw_evidence if isinstance(raw_evidence, dict) else {}
        evidence_text = " ".join(str(value) for value in raw_evidence) if isinstance(raw_evidence, (list, dict)) else str(raw_evidence)
        source_module = str(evidence.get("source_module", ""))
        if not source_module and evidence_text:
            source_module = next((part.replace("/", ".").removesuffix(".py").replace("brasfoot_engine.", "") for part in evidence_text.split() if "/engine/core/" in part or "engine/core/" in part), "")
        module_path = MODULE_BASE / (source_module.replace(".", "/") + ".py") if source_module.startswith("engine.") else None
        module_exists = bool(module_path and module_path.exists())
        domain = str(item.get("title", ""))
        token = re.sub(r"[^a-z0-9_]+", "_", domain.lower()).strip("_")
        career_link = token in career.lower() or source_module.rsplit(".", 1)[-1].replace("_contract", "") in career.lower() or "manager service" in evidence_text.lower() or "manager_service" in evidence_text.lower() or "career.py" in evidence_text
        gateway_link = token in gateway.lower() or source_module.rsplit(".", 1)[-1].replace("_contract", "") in gateway.lower() or "gateway" in evidence_text.lower() or "career_gateway.py" in evidence_text
        problems = []
        if item.get("status") != "DONE": problems.append("manifest_item_not_done")
        if source_module and not module_exists: problems.append("source_module_missing")
        item_source_of_truth = evidence.get("source_of_truth") or global_source_of_truth
        if item_source_of_truth != "SQL_GAMESTATE": problems.append("source_of_truth_mismatch")
        if source_module and not career_link: problems.append("manager_service_link_not_proven")
        if source_module and not gateway_link: problems.append("gateway_link_not_proven")
        findings.append({"item_id": item.get("item_id"), "status": "PASS" if not problems else "REVIEW", "problems": problems, "source_module": source_module, "module_exists": module_exists, "manager_service_link": career_link, "gateway_link": gateway_link})
    summary = {"total": len(items), "pass": sum(x["status"] == "PASS" for x in findings), "review": sum(x["status"] == "REVIEW" for x in findings), "manifest_summary": manifest.get("summary"), "source_of_truth": "SQL_GAMESTATE"}
    output = {"summary": summary, "findings": findings}
    hard_findings = [item for item in findings if any(problem != "source_of_truth_mismatch" for problem in item["problems"])]
    output["summary"]["hard_findings"] = len(hard_findings)
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
