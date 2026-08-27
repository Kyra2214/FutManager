from __future__ import annotations

from engine.database.repositories import PlayerRepository, TeamPlayerRepository
from engine.players.domain import Player


class PlayerEngine:
    """Serviço de jogadores baseado em consulta sob demanda ao banco."""

    def __init__(self, player_repository: PlayerRepository, team_player_repository: TeamPlayerRepository):
        self.players = player_repository
        self.team_players = team_player_repository

    def get(self, player_id: int) -> Player | None:
        row = self.players.get(player_id)
        if row is None:
            return None
        return self._to_domain(row)

    def search(self, name: str, limit: int = 50) -> list[Player]:
        return [self._to_domain(row) for row in self.players.search(name, limit)]

    def get_by_team(self, team_id: int, limit: int = 1000) -> list[Player]:
        return [self._to_domain(row) for row in self.players.database.open().execute(
            """SELECT j.*, jt.status FROM jogadores j
               JOIN jogador_time jt ON jt.jogador_id=j.jogador_id
               WHERE jt.time_id=? ORDER BY j.nome LIMIT ?""", (team_id, limit))]

    def teams_for_player(self, player_id: int, limit: int = 1000):
        return self.team_players.teams_for_player(player_id, limit)

    @staticmethod
    def _to_domain(row) -> Player:
        # Status é atributo do vínculo, não do jogador canônico.
        return Player.from_row(row, row["status"] if "status" in row.keys() else None)
