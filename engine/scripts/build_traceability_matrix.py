from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "frontend" / "docs" / "roadmap_3000_execucao.json"
AUDIT = ROOT / "docs" / "audit" / "roadmap_3000_final.json"
OUT_JSON = ROOT / "docs" / "audit" / "traceability_matrix_611.json"
OUT_MD = ROOT / "docs" / "audit" / "traceability_matrix_611.md"


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    items = {int(item["item_id"]): item for item in manifest["items"]}
    reviewed = [finding for finding in audit["findings"] if finding["status"] == "REVIEW"]
    rows = []
    for finding in reviewed:
        item = items.get(int(finding["item_id"]), {})
        rows.append({
            "item_id": int(finding["item_id"]),
            "priority": item.get("priority"),
            "title": item.get("title"),
            "problems": finding.get("problems", []),
            "source_module": finding.get("source_module", ""),
            "module_exists": bool(finding.get("module_exists")),
            "manager_service_link": bool(finding.get("manager_service_link")),
            "gateway_link": bool(finding.get("gateway_link")),
            "next_evidence": "apontar módulo/método/teste canônico" if "source_module_missing" in finding.get("problems", []) else "apontar vínculo explícito no ManagerService/gateway",
        })
    counts = Counter(problem for row in rows for problem in row["problems"])
    output = {
        "schema": "futmanager-traceability-v1",
        "source_of_truth": "SQL_GAMESTATE",
        "manifest_total": len(items),
        "review_total": len(rows),
        "problem_counts": dict(sorted(counts.items())),
        "rows": rows,
    }
    OUT_JSON.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Matriz de rastreabilidade dos itens em revisão",
        "",
        f"A matriz contém **{len(rows)} itens** que o auditor estrutural classificou como `REVIEW`. O status do manifesto permanece independente: os 3.000 itens continuam `DONE`. A fonte única é **SQL/GameState**.",
        "",
        "## Distribuição dos achados",
        "",
        "| Achado | Ocorrências | Interpretação |",
        "|---|---:|---|",
    ]
    meanings = {
        "source_module_missing": "O módulo indicado pela evidência não foi localizado na árvore atual.",
        "manager_service_link_not_proven": "A heurística não encontrou vínculo explícito no ManagerService.",
        "gateway_link_not_proven": "A heurística não encontrou vínculo explícito no gateway.",
    }
    for key, count in sorted(counts.items()):
        lines.append(f"| `{key}` | {count} | {meanings.get(key, 'Requer revisão manual.') } |")
    lines += ["", "## Itens", "", "| ID | Prioridade | Problemas | Módulo | Próxima evidência |", "|---:|---|---|---|---|"]
    for row in rows:
        module = row["source_module"] or "evidência legada sem módulo explícito"
        problems = ", ".join(f"`{problem}`" for problem in row["problems"])
        lines.append(f"| {row['item_id']} | {row['priority']} | {problems} | `{module}` | {row['next_evidence']} |")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "review_total": len(rows), "problem_counts": dict(sorted(counts.items()))}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
