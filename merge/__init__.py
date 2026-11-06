"""BugfixedHL x Opposing Force Speedrun Merge Kit.

Public API is intentionally tiny: load a manifest, resolve the pinned source
trees, and run :class:`merge.engine.MergeEngine`.
"""

from .engine import MergeEngine, MergeError
from .manifest import ManifestError, load_plan, load_upstreams, validate_plan

__all__ = [
    "MergeEngine",
    "MergeError",
    "ManifestError",
    "load_plan",
    "load_upstreams",
    "validate_plan",
]
__version__ = "0.1.0"
