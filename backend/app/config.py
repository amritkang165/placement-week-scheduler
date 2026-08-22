"""Application configuration.

Environment-driven settings (database, CORS, app env) plus the tunable
solver/objective configuration used by the scheduling engine.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/placement_scheduler"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    solver_time_limit_seconds: float = 10.0
    solver_workers: int = 8

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@dataclass
class SolverWeights:
    """Objective-function weights (see objective.py for reasoning).

    All weights are configurable so the trade-offs can be tuned without
    touching solver code.
    """

    scheduled_interview: int = 10000  # maximize coverage (dominant)
    priority: dict[str, int] = field(  # bonus per scheduled interview by tier
        default_factory=lambda: {"TIER_1": 300, "TIER_2": 200, "TIER_3": 100}
    )
    earliness_minute: int = 1         # pack interviews -> reduce waiting (tie-breaker)
    moved_interview: int = 5000       # penalize any moved appointment (replan)
    moved_minute: int = 5             # penalize each minute shifted (replan)


@dataclass
class SolverConfig:
    """CP-SAT solver configuration."""

    time_limit_seconds: float = 10.0
    num_search_workers: int = 8
    weights: SolverWeights = field(default_factory=SolverWeights)


settings = Settings()
solver_config = SolverConfig(
    time_limit_seconds=settings.solver_time_limit_seconds,
    num_search_workers=settings.solver_workers,
)
