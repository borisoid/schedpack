from typing import (
    Any,
    Callable,
    Iterable,
    Optional,
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
    PeriodicTimeSpan_WithExtraConditions,
)


class PeriodicActivity(
    PeriodicTimeSpan,
    PeriodicActivity_ABC,
):
    def __init__(
        self,
        *,
        payload: Any,
        periodic_time_point: PeriodicTimePoint_ABC,
        duration: seconds,
    ):
        super().__init__(
            periodic_time_point=periodic_time_point,
            duration=duration,
        )
        self.payload = payload


class PeriodicActivity_WithExtraConditions(
    PeriodicTimeSpan_WithExtraConditions,
    PeriodicActivity_ABC,
):
    def __init__(
        self,
        *,
        payload: Any,
        periodic_time_point: PeriodicTimePoint_ABC,
        duration: seconds,
        extra_conditions: Optional[Iterable[
            Callable[[Instrumented_StaticTimeSpan_ABC], bool]
        ]] = None,
        extra_conditions_any: bool = False,
    ):
        super().__init__(
            periodic_time_point=periodic_time_point,
            duration=duration,
            extra_conditions=extra_conditions,
            extra_conditions_any=extra_conditions_any,
        )
        self.payload = payload
