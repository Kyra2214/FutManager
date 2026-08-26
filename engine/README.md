# Brasfoot + F1 Manager — Esqueleto do Motor

Este projeto contém exclusivamente o esqueleto técnico inicial do motor de gerenciamento de futebol. O banco SQLite real está em `data/database/game.db` e a cópia controlada de uma nova carreira está em `data/state/game.db`.

## Escopo implementado

A estrutura inclui `GameState`, `WorldState`, `PersistenceService`, acesso centralizado ao SQLite e repositórios para jogadores, times, países, vínculos jogador-time e atributos nativos. Também existem contratos estruturais para scouting, transferências, finanças, comissão técnica, estádio, patrocinadores e simulação.

Nenhum frontend, partida, temporada, IA, mercado funcional, evolução, scouting real, economia real ou animação foi implementado nesta etapa.

## Uso mínimo

```python
from engine.core.engine import FootballManagerEngine

engine = FootballManagerEngine("data/database/game.db").open()
players = engine.players.search("Neymar")
clubs = engine.teams.search("Flamengo")
state = engine.create_game_state()
engine.close()
```

## Regra de dados

A tabela `jogadores` possui uma única entidade canônica por atleta. Aparições em múltiplos clubes são representadas em `jogador_time`, preservando categoria e status do vínculo. As posições são mantidas como: 0 Goleiro, 1 Lateral, 2 Zagueiro, 3 Meia e 4 Atacante.

## Validação

Execute:

```bash
PYTHONPATH=. pytest -q tests/test_engine.py
```

O relatório detalhado está em `engine_skeleton_report.txt`.
