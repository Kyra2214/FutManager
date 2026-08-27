from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from random import Random


@dataclass(frozen=True)
class LifecycleConfig:
    initial_age: int = 16
    professional_age: int = 18
    peak_start_age: int = 23
    peak_end_age: int = 28
    likely_peak_start_age: int = 26
    likely_peak_end_age: int = 27
    decline_start_age: int = 32
    retirement_min_age: int = 35


class PotentialTier(StrEnum):
    LOW = "baixo"
    MEDIUM = "médio"
    GOOD = "bom"
    STAR = "craque"
    SUPERSTAR = "supercraque"
    PHENOMENON = "fenômeno"


@dataclass(frozen=True)
class PlayerGenerationRequest:
    country_id: int
    team_id: int | None = None
    position_code: int | None = None
    seed: int | None = None


@dataclass(frozen=True)
class PlayerGenerationResult:
    initial_age: int
    potential_tier: PotentialTier
    country_id: int
    team_id: int | None
    position_code: int | None


class PlayerGenerationService:
    """Contrato preparado para a futura geração; não cria jogadores nesta etapa."""
    def __init__(self, config: LifecycleConfig | None = None):
        self.config = config or LifecycleConfig()

    def plan_generation(self, request: PlayerGenerationRequest) -> PlayerGenerationResult:
        # Somente planejamento determinístico do contrato; persistência e roleta serão futuras.
        rng = Random(request.seed)
        tier = rng.choices(list(PotentialTier), weights=[45, 30, 15, 7, 2.5, 0.5])[0]
        return PlayerGenerationResult(self.config.initial_age, tier, request.country_id, request.team_id, request.position_code)


class PlayerLifecycleService:
    """Ponto de extensão para evolução, declínio e aposentadoria; sem mutação ainda."""
    def age_player(self, *_args, **_kwargs):
        raise NotImplementedError("O ciclo de vida será implementado em etapa posterior.")

    def retire_player(self, *_args, **_kwargs):
        raise NotImplementedError("A aposentadoria será implementada em etapa posterior.")
