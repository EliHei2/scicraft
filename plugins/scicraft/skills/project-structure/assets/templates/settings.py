"""Every setting of {{NAME}}, in one place. Scripts and notebooks call preset(); none copies a value.

    from {{PKG}}.settings import preset
    cfg = preset("quick")                         # laptop smoke run, minutes; writes to scratch/
    cfg = preset("full", n_items=None, seed=1)    # overrides by keyword only; an unknown key raises

A notebook's parameters cell is one call to preset(). A script takes --profile and --set KEY=VALUE
and calls the same function, so the notebook and the scripts can never disagree.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

PROJECT = Path(__file__).resolve().parents[2]   # src/<pkg>/settings.py -> project root; no cwd dependence


@dataclass
class Config:
    """One field per setting, each with a comment. [Replace the example fields with the project's own.]"""

    profile: str = "quick"
    seed: int = 0
    # data
    n_items: Optional[int] = 3            # [example] datasets to load, smallest first; None = all
    max_rows: int = 256                   # [example] equal row budget for every table
    # models or methods compared
    variants: tuple = ("baseline",)       # [example] one view per variant under views/<variant>/
    # evaluation
    n_boot: int = 200                     # [example] bootstrap resamples
    # hardware
    device: str = "auto"                  # auto | cuda | mps | cpu
    extra: dict = field(default_factory=dict)

    @property
    def results(self) -> Path:
        """One results root per profile. The smoke profile writes to scratch/ and is never cited."""
        if self.profile == "quick":
            return PROJECT / "scratch" / "quick"
        return PROJECT / "results" / "runs" / self.profile

    def to_dict(self) -> dict:
        return asdict(self)


# Named presets. A new hardware profile (a laptop GPU, a hosted notebook, a cluster node) is a new
# entry here and gets its own results root; two profiles never share one.
PRESETS: dict = {
    "quick": {},
    "full": {"n_items": None, "max_rows": 1024, "n_boot": 1000},
}


def preset(name: str = "quick", **overrides: Any) -> Config:
    if name not in PRESETS:
        raise KeyError(f"unknown preset {name!r}; known: {sorted(PRESETS)}")
    cfg = Config(profile=name, **PRESETS[name])
    for key, value in overrides.items():
        if not hasattr(cfg, key):
            raise KeyError(f"unknown setting {key!r}")
        setattr(cfg, key, value)
    return cfg
