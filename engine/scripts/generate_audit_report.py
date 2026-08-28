#!/usr/bin/env python3
"""Generate the executive audit report from machine-readable repository artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from count_tests import count_python_tests, count_vitest_tests


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def generate(manifest_path: Path, output_path: Path, python_root: Path, vitest_root: Path, counts_path: Path | None) -> None:
    manifest = load_json(manifest_path)
    summary = manifest["summary"]
    manifest_summary = summary["manifest_summary"]
    python = count_python_tests(python_root)
    vitest = count_vitest_tests(vitest_root)
    counts = {"python": python, "vitest": vitest, "total": python["cases"] + vitest["cases"]}
    if counts_path:
        counts_path.parent.mkdir(parents=True, exist_ok=True)
        counts_path.write_text(json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = f"""# Relatório pós-roadmap do FutManager

> Este arquivo é gerado por `engine/scripts/generate_audit_report.py`. Os números abaixo não são digitados manualmente: o auditor estrutural é lido de `docs/audit/roadmap_3000_final.json` e os testes são contados diretamente no código versionado.

## Escopo

Esta rodada consolida a auditoria do manifesto, a integração frontend–gateway–GameState, o isolamento de fixtures e os gates de entrega. A regra arquitetural permanece: **SQL/GameState é a fonte única da verdade**.

## Resultado executivo

| Área | Resultado | Evidência gerada |
|---|---:|---|
| Manifesto | {manifest_summary['done']} itens `DONE`, {manifest_summary['pending']} pendentes de {manifest_summary['total']} | `frontend/docs/roadmap_3000_execucao.json` |
| Auditor estrutural | {summary['pass']} aprovados, {summary['review']} em revisão de {summary['total']} | `docs/audit/roadmap_3000_final.json` |
| Testes Python | {python['cases']} casos em {python['files']} arquivos | `docs/audit/test_counts.json` |
| Testes Vitest | {vitest['cases']} casos em {vitest['files']} arquivos | `docs/audit/test_counts.json` |
| Total de testes descobertos | {counts['total']} casos | `engine/scripts/count_tests.py` |
| Fonte da verdade | `{summary['source_of_truth']}` | Manifesto estrutural |
| Itens em revisão estrutural | {summary['hard_findings']} | Manifesto estrutural |

## Leitura correta da auditoria

O status `REVIEW` do auditor estrutural não significa que o manifesto tenha itens pendentes. Ele representa a quantidade de itens cuja evidência estrutural ainda não prova algum vínculo específico de módulo, serviço ou gateway. O manifesto bruto e a auditoria estrutural são visões diferentes do mesmo escopo e permanecem publicados separadamente.

## Integridade do pacote

O pipeline valida os manifestos `.sha256` contra seus arquivos `.gz` correspondentes, verifica a integridade SQLite dos bancos descompactados e rejeita o banco-semente de release quando as tabelas `manager_careers`, `managers` ou `manager_selection_assignments` contêm qualquer linha. A validação ocorre antes das suítes de testes e das simulações demoradas.

## Portabilidade do backend web

Os leitores de estado e assets usam `FUTMANAGER_ENGINE_ROOT` e `FUTMANAGER_ENGINE_STATE_PATH`, com fallback relativo ao checkout quando aplicável. O teste de integração de carreira usa um banco temporário derivado da configuração do ambiente, permitindo reproduzir o fluxo fora da máquina que originou o pacote.

## Validação e limitações

Os resultados de execução do CI devem ser lidos nos artefatos do workflow correspondente; este documento não transforma uma contagem de testes em alegação de aprovação. A auditoria estrutural continua registrando {summary['review']} itens em revisão, e a validação Android depende do projeto da branch `offline-android-release`, que é auditado e integrado separadamente do backend web.

## Fonte de geração

Para regenerar este relatório e os contadores após qualquer alteração no código, execute:

```bash
python3 engine/scripts/generate_audit_report.py
```
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("docs/audit/roadmap_3000_final.json"))
    parser.add_argument("--output", type=Path, default=Path("docs/audit/relatorio_pos_roadmap.md"))
    parser.add_argument("--python-root", type=Path, default=Path("engine/tests"))
    parser.add_argument("--vitest-root", type=Path, default=Path("."))
    parser.add_argument("--counts", type=Path, default=Path("docs/audit/test_counts.json"))
    args = parser.parse_args()
    generate(args.manifest, args.output, args.python_root, args.vitest_root, args.counts)
    print(f"Generated {args.output} using {args.manifest}")


if __name__ == "__main__":
    main()
