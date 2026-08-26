from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine.players.lifecycle import LifecycleConfig, PlayerGenerationRequest, PlayerGenerationService, PotentialTier, PlayerLifecycleService


def test_generation_is_parameterized_and_not_persisted():
    service = PlayerGenerationService(LifecycleConfig(initial_age=16))
    result = service.plan_generation(PlayerGenerationRequest(country_id=29, seed=7))
    assert result.initial_age == 16
    assert result.country_id == 29
    assert isinstance(result.potential_tier, PotentialTier)


def test_lifecycle_behavior_is_deferred():
    try:
        PlayerLifecycleService().age_player(None)
    except NotImplementedError:
        pass
    else:
        raise AssertionError("ciclo de vida não deve estar implementado nesta etapa")
