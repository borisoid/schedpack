from datetime import (
    datetime,
    timedelta,
)
from typing import (
    Any,
    Optional,
    Union,
    overload,
)

from .abstraction.abc import (
    Instrumented_StaticTimeSpan_ABC,
    StaticTimeSpan_ABC,
)
from .abstraction.non_existent_time_span import (
    NonExistentTimeSpanType,
)
from .abstraction.types import (
    seconds,
)


class Instrumented_StaticTimeSpan_Factory:

    # create {{{

    # overloads {{{

    @overload
    @classmethod
    def create(
        cls,
        *,
        start: datetime,
        end: datetime,
    ) -> Instrumented_StaticTimeSpan_ABC:
        ...

    @overload
    @classmethod
    def create(
        cls,
        *,
        start: datetime,
        duration: seconds,
    ) -> Instrumented_StaticTimeSpan_ABC:
        ...

    @overload
    @classmethod
    def create(
        cls,
        *,
        end: datetime,
        duration: seconds,
    ) -> Instrumented_StaticTimeSpan_ABC:
        ...

    # }}} overloads

    @classmethod
    def create(
        cls,
        *,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        duration: Optional[seconds] = None,
    ) -> Instrumented_StaticTimeSpan_ABC:

        result = Instrumented_StaticTimeSpan()

        if start is not None and duration is not None:
            result.start = start
            result.end = start + timedelta(seconds=duration)
        elif start is not None and end is not None:
            result.start = start
            result.end = end
        elif end is not None and duration is not None:
            result.start = end - timedelta(seconds=duration)
            result.end = end
        else:
            raise ValueError(
                "Must specify two of these: start, end, duration"
            )

        return result

    # }}} create


class Instrumented_StaticTimeSpan(Instrumented_StaticTimeSpan_ABC):
    def __hash__(self) -> int:
        return hash((self.start, self.end))

    def __eq__(self, other: Any) -> bool:
        return issubclass(other, StaticTimeSpan_ABC) and (
            self.start == other.start and self.end == other.end
        )

    def __lt__(
        self,
        other: Union[Instrumented_StaticTimeSpan_ABC, NonExistentTimeSpanType],
    ) -> bool:
        if isinstance(other, NonExistentTimeSpanType):
            return True
        return self.start < other.start

    def __gt__(
        self,
        other: Union[Instrumented_StaticTimeSpan_ABC, NonExistentTimeSpanType],
    ) -> bool:
        if isinstance(other, NonExistentTimeSpanType):
            return False
        return self.start > other.start
