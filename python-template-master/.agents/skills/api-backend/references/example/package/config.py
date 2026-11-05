"""Configuration, read once from the environment (`docs/LAYOUT.md`, rule 7)."""

import dataclasses
import os
import typing

__all__ = ["Settings", "settings"]


@dataclasses.dataclass(slots=True)
class Settings:
    """The runtime settings. Tests replace `database_url`."""

    database_url: str = os.environ.get("DATABASE_URL", "postgresql://app:app@localhost:5432/app")


settings: typing.Final = Settings()
