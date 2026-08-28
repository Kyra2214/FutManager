# Evidência de preparação inicial híbrida

## Escopo

Esta validação cobre a parte que a inspeção estática do APK não consegue provar: o pacote remoto baixado na primeira execução contém um GameState íntegro e sem carreira pré-populada.

## Comando executado

```bash
python3 scripts/validate-data-package.py \
  /tmp/futmanager-data-v1/futmanager-data-v1.0.0.zip \
  /tmp/futmanager-data-v1/manifest.json
```

## Resultado

| Campo | Resultado |
|---|---:|
| Versão | `v1.0.0` |
| Tamanho do pacote | `83.066.627 bytes` |
| SHA-256 do pacote | `87bf51ce29cac3fe4f1da79fc87d594610be1a2343c19cb195b58c7b14d6f114` |
| Tamanho do banco extraído | `119.455.744 bytes` |
| `PRAGMA integrity_check` | `ok` |
| `manager_careers` | `0` |
| `managers` | `0` |
| `manager_selection_assignments` | `0` |

O resultado confirma que o ZIP remoto corresponde ao manifesto, contém `database/game.db`, possui índices obrigatórios e usa um seed limpo. Ele não substitui o teste em aparelho: a instalação física ainda deve confirmar a tela de preparação, a conclusão do download, a criação de carreira e a reabertura offline.

## Interpretação

A garantia da carreira inicial limpa é dividida em duas evidências. O validador do APK confirma que o banco não foi embutido. Este gate confirma que o banco que será baixado é íntegro e não contém carreira pré-criada. Juntos, os dois resultados descrevem o fluxo híbrido real sem afirmar que o APK contém o banco.
