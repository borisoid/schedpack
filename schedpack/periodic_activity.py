from typing import (
    Any,
    Callable,
    Iterable,
)

from .abstraction.abc import (
    Instrumented_StaticTimeSpan_ABC,
    PeriodicActivity_ABC,
    PeriodicTimePoint_ABC,
)
from .abstraction.types import (
    seconds,
)
from .periodic_time_span import (
    PeriodicTimeSpan,
    PeriodicTimeSpanWithExtraConditions,
)


class PeriodicActivity(
    PeriodicTimeSpan,
    PeriodicActivity_ABC,
):
    def __init__(
        self,
        payload: Any,
        period_engine: PeriodicTimePoint_ABC,
        duration: seconds,
    ):
        super().__init__(period_engine, duration)
        self.payload = payload


class PeriodicActivityWithExtraConditions(
    PeriodicTimeSpanWithExtraConditions,
    PeriodicActivity_ABC,
):
    def __init__(
        self,
        payload: Any,
        period_engine: PeriodicTimePoint_ABC,
        duration: seconds,
        extra_conditions: Iterable[
            Callable[[Instrumented_StaticTimeSpan_ABC], bool]
        ] = None,
        extra_conditions_any: bool = False,
    ):
        super().__init__(
            period_engine,
            duration,
            extra_conditions,
            extra_conditions_any,
        )
        self.payload = payload
