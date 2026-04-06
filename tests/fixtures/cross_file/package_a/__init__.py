"""Package A: Defines frozen models with @nodiscard methods."""

from nodiscard._marker import NoDiscard as NoDiscard
from nodiscard.models import FrozenModel as FrozenModel

__all__ = ["FrozenModel", "NoDiscard"]
