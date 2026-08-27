from pathlib import Path

from engine.core.state import GameState, PersistenceService
from engine.database.repositories import Database, PlayerRepository, TeamRepository, CountryRepository, TeamPlayerRepository, PlayerAttributeRepository
from engine.players.player_engine import PlayerEngine


class FootballManagerEngine:
    def __init__(self, database_path: str | Path):
        self.database = Database(database_path)
        self.players_repository = PlayerRepository(self.database)
        self.teams = TeamRepository(self.database)
        self.countries = CountryRepository(self.database)
        self.team_players = TeamPlayerRepository(self.database)
        self.player_attributes = PlayerAttributeRepository(self.database)
        self.players = PlayerEngine(self.players_repository, self.team_players)
        self.persistence = PersistenceService(database_path)

    def open(self) -> "FootballManagerEngine":
        self.database.open()
        return self

    def close(self) -> None:
        self.database.close()

    def create_game_state(self, country_id=None, controlled_team_id=None) -> GameState:
        return GameState.initialize(self.database.path, country_id, controlled_team_id)
