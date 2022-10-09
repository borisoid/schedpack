from datetime import (
    datetime,
)
from typing import (
    Any,
)

from .abstraction.abc import (
    StaticTimeSpan_ABC,
)


class ResolvedActivity(StaticTimeSpan_ABC):
    """An activity with known start/end time"""

    def __init__(
        self,
        payload: Any,
        *,
        start: datetime,
        end: datetime,
    ):
        self.payload = payload
        self.start = start
        self.end = end

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
                f"payload={self.payload!r},"
                f"start=<{self.start!s}>,"
                f"end=<{self.end!s}>"
            ")"
        )
