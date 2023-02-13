from datetime import (
    datetime,
    timedelta,
)
from typing import (
    Callable,
    Iterable,
    Literal,
    Optional,
    Tuple,
    Union,
    overload,
)

from .abstraction.abc import (
    Instrumented_StaticTimeSpan_ABC,
    PeriodicTimePoint_ABC,
    PeriodicTimeSpan_ABC,
)
from .abstraction.non_existent_time_span import (
    NonExistentTimeSpan,
    NonExistentTimeSpanType,
)
from .abstraction.periodic_time_span.extra_conditions_max_fails import (
    ExtraConditionsMaxFails
)
from .abstraction.types import (
    seconds,
)
from .instrumented_static_time_span import (
    Instrumented_StaticTimeSpan_Factory,
)


class PeriodicTimeSpan(PeriodicTimeSpan_ABC):
    def __init__(
        self,
        *,
        periodic_time_point: PeriodicTimePoint_ABC,
        duration: seconds,
    ):
        self.periodic_time_point = periodic_time_point
        self.duration = duration

    def is_ongoing(self, moment: datetime) -> bool:
        return self.get_current(moment) is not NonExistentTimeSpan

    def get_current(
        self,
        moment: datetime,
    ) -> Union[Instrumented_StaticTimeSpan_ABC, NonExistentTimeSpanType]:
        next = self.periodic_time_point.get_next(moment)
        current = self.periodic_time_point.get_next(
            moment - timedelta(seconds=self.duration)
        )
        if current and ((not next) or (next > current)):
            return Instrumented_StaticTimeSpan_Factory.create(
                start=current,
                duration=self.duration,
            )
        return NonExistentTimeSpan

    def get_next(
        self,
        moment: datetime,
    ) -> Union[Instrumented_StaticTimeSpan_ABC, NonExistentTimeSpanType]:
        if start := self.periodic_time_point.get_next(moment):
            return Instrumented_StaticTimeSpan_Factory.create(
                start=start,
                duration=self.duration,
            )
        return NonExistentTimeSpan

    # get_current_or_next {{{

    # overloads {{{

    @overload
    def get_current_or_next(
        self,
        moment: datetime,
        *,
        return_is_current: Literal[False],
    ) -> Union[Instrumented_StaticTimeSpan_ABC, NonExistentTimeSpanType]:
        ...

    @overload
    def get_current_or_next(
        self,
        moment: datetime,
        *,
        return_is_current: Literal[True],
    ) -> Tuple[
        Union[
            Instrumented_StaticTimeSpan_ABC,
            NonExistentTimeSpanType,
        ],
        Optional[bool],
    ]:
        ...

    # }}} overloads

    def get_current_or_next(
        self,
        moment: datetime,
        *,
        return_is_current: bool = False,
    ) -> Union[
        Union[
            Instrumented_StaticTimeSpan_ABC,
            NonExistentTimeSpanType,
        ],
        Tuple[
            Union[
                Instrumented_StaticTimeSpan_ABC,
                NonExistentTimeSpanType,
            ],
            Optional[bool],
        ],
    ]:
        span = self.get_current(moment)
        if not isinstance(span, NonExistentTimeSpanType):
            return (span, True) if return_is_current else span

        span = self.get_next(moment)
        if not isinstance(span, NonExistentTimeSpanType):
            return (span, False) if return_is_current else span

        span = NonExistentTimeSpan
        return (span, None) if return_is_current else span

    # }}} get_current_or_next


class PeriodicTimeSpan_WithExtraConditions(PeriodicTimeSpan):

    DEFAULT_EXTRA_CONDITIONS_MAX_FAILS = 20

    def __init__(
        self,
        *,
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
        )
        self.extra_conditions = extra_conditions
        self.extra_conditions_any = extra_conditions_any

    def extra_conditions_ok(
        self,
        span: Instrumented_StaticTimeSpan_ABC,
    ) -> bool:
        if not self.extra_conditions:
            return True

        return (
            any(map(lambda ec: ec(span), self.extra_conditions))
            if self.extra_conditions_any else
            all(map(lambda ec: ec(span), self.extra_conditions))
        )

    def get_current(
        self,
        moment: datetime,
    ) -> Union[
        Instrumented_StaticTimeSpan_ABC,
        NonExistentTimeSpanType,
    ]:
        span = super().get_current(moment)
        if not isinstance(span, NonExistentTimeSpanType) and self.extra_conditions_ok(span):
            return span
        return NonExistentTimeSpan

    def get_next(
        self,
        moment: datetime,
        *,
        extra_conditions_max_fails: Union[
            Literal[ExtraConditionsMaxFails.NOT_SPECIFIED],
            int,
            None,
        ] = ExtraConditionsMaxFails.NOT_SPECIFIED,
    ) -> Union[
        Instrumented_StaticTimeSpan_ABC,
        NonExistentTimeSpanType,
    ]:
        if extra_conditions_max_fails is ExtraConditionsMaxFails.NOT_SPECIFIED:
            extra_conditions_max_fails = self.DEFAULT_EXTRA_CONDITIONS_MAX_FAILS

        span: Union[
            Instrumented_StaticTimeSpan_ABC,
            NonExistentTimeSpanType,
        ] = Instrumented_StaticTimeSpan_Factory.create(start=moment, duration=0)
        assert not isinstance(span, NonExistentTimeSpanType)
        while True:
            span = super().get_next(span.start)
            if not isinstance(span, NonExistentTimeSpanType):
                if not self.extra_conditions_ok(span):
                    if extra_conditions_max_fails is not None:
                        extra_conditions_max_fails -= 1
                        if extra_conditions_max_fails <= 0:
                            return NonExistentTimeSpan
                    else:
                        continue
                else:
                    break
            else:
                break

        return span
