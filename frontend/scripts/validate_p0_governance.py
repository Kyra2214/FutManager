from pathlib import Path

REQUIRED = (
    "## Matriz item→evidência dos 20 passos P0-1",
    "| 1 |", "| 20 |",
    "## Riscos e respostas",
    "## Responsabilidades",
    "Matriz de dependências",
    "descoberta, construção, validação e concluída",
    "escopo essencial, avançado e experimental",
    "níveis P0, P1 e P2",
    "dívida técnica",
    "ARQUIVO-MÃE → SQL/GameState",
    "PRAGMA integrity_check = ok",
    "PRAGMA foreign_key_check",
    "P1 e P2 permanecem bloqueados",
    "Nenhum jogador, clube, saldo, resultado",
    "seed persistida",
    "idempotentes, monotônicas",
    "não fazem commit implícito",
    "não grava nem calcula estado de jogo",
    "hash imutável",
)

path = Path(__file__).resolve().parents[1] / "docs" / "p0_front_01_governance_charter.md"
text = path.read_text(encoding="utf-8")
missing = [phrase for phrase in REQUIRED if phrase not in text]
if missing:
    raise SystemExit("P0_GOVERNANCE_CHARTER_INCOMPLETE:" + ",".join(missing))
rows = [line for line in text.splitlines() if line.startswith("| ") and line.count("|") >= 3]
item_rows = {line.split("|")[1].strip() for line in rows if line.split("|")[1].strip().isdigit()}
if not set(map(str, range(1, 21))).issubset(item_rows):
    raise SystemExit("P0_GOVERNANCE_ITEM_MATRIX_INCOMPLETE")
print({"charter": str(path), "criteria_checked": len(REQUIRED), "item_evidence_rows": len(set(map(str, range(1, 21))) & item_rows), "status": "VALID"})
