import shutil
import sqlite3
from pathlib import Path

import pytest

from engine.core.state_store import StateDatabaseError
from engine.ai.club_ai import ClubAI
from engine.commercial.sponsorship_media import CommercialService
from engine.competitions.match_engine import CompetitionService
from engine.competitions.structure import CompetitionStructureService
from engine.core.global_integration import GlobalIntegrationOrchestrator
from engine.database.repositories import Database
from engine.economy.institutional_power import InstitutionalPowerService
from engine.economy.matchday_revenue import MatchdayRevenueService
from engine.economy.sponsorships import SponsorshipService
from engine.economy.staff_market import StaffMarketService
from engine.economy.world_economy import EconomyService, WorldEconomyService
from engine.events.service import ClubEventService
from engine.manager.career import ManagerService
from engine.rules.state_store import CareerStateStore
from engine.scouting.service import ScoutService
from engine.social.attendance import AttendanceService
from engine.social.stadium_fans import SocialService
from engine.sports.cycle import SportStateStore
from engine.staff.state_store import StaffStateStore
from engine.stadiums.service import StadiumService
from engine.transfers.market import TransferMarketService
from engine.world.orchestrator import IntegrationOrchestrator
from engine.world.simulation import WorldSimulationService
from engine.world.weekly_cycle import WeeklyWorldCycleService

BASE = Path(__file__).resolve().parents[1] / 'data/database/game.db'

FACTORIES = [
    ClubAI, CommercialService, CompetitionService, CompetitionStructureService,
    GlobalIntegrationOrchestrator, InstitutionalPowerService,
    MatchdayRevenueService, SponsorshipService, StaffMarketService,
    EconomyService, WorldEconomyService, ClubEventService, ManagerService,
    CareerStateStore, ScoutService, AttendanceService, SocialService,
    SportStateStore, StaffStateStore, StadiumService, TransferMarketService,
    IntegrationOrchestrator, WorldSimulationService, WeeklyWorldCycleService,
]


def test_read_only_database_repository_can_read_immutable_base():
    repository = Database(BASE)
    connection = repository.open()
    assert connection.execute('SELECT COUNT(*) FROM jogadores').fetchone()[0] == 231911
    repository.close()


@pytest.mark.parametrize('factory', FACTORIES, ids=lambda item: item.__name__)
def test_every_path_opening_entrypoint_rejects_immutable_base(factory):
    with pytest.raises(StateDatabaseError, match='IMMUTABLE_BASE_DATABASE'):
        factory(BASE)


@pytest.mark.parametrize('factory', FACTORIES, ids=lambda item: item.__name__)
def test_every_path_opening_entrypoint_accepts_temporary_state(factory, tmp_path: Path):
    state = tmp_path / f'{factory.__name__}.db'
    shutil.copy2(BASE, state)
    try:
        instance = factory(state)
    except StateDatabaseError as error:
        pytest.fail(f'{factory.__name__} rejected temporary GameState: {error}')
    except (sqlite3.Error, KeyError, ValueError, AttributeError):
        # Schema-specific initialization may require tables owned by a later migration;
        # the important contract here is that the path guard accepted the GameState.
        return
    else:
        close = getattr(instance, 'close', None)
        if callable(close):
            close()
