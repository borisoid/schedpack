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
    NON_EXISTENT_TIME_SPAN,
    NonExistentTimeSpan,
)
from .abstraction.types import (
    seconds,
)
from .static_time_span import (
    Instrumented_StaticTimeSpan_Factory,
)
from .utils.periodic_time_span import (
    ExtraConditionsMaxFails,
)


class PeriodicTimeSpan(PeriodicTimeSpan_ABC):
    def __init__(
        self,
        period_engine: PeriodicTimePoint_ABC,
        duration: seconds,
    ):
        self.period_engine = period_engine
        self.duration = duration

    def is_ongoing(self, moment: datetime) -> bool:
        return self.get_current(moment) is not NON_EXISTENT_TIME_SPAN

    def get_current(
        self,
        moment: datetime,
    ) -> Union[Instrumented_StaticTimeSpan_ABC, NonExistentTimeSpan]:
        next = self.period_engine.get_next(moment)
        current = self.period_engine.get_next(
            moment - timedelta(seconds=self.duration)
        )
        if current and ((not next) or (next > current)):
            return Instrumented_StaticTimeSpan_Factory.create(
                start=current,
                duration=self.duration,
            )
        return NON_EXISTENT_TIME_SPAN

    def get_next(
        self,
        moment: datetime,
    ) -> Union[Instrumented_StaticTimeSpan_ABC, NonExistentTimeSpan]:
        if start := self.period_engine.get_next(moment):
            return Instrumented_StaticTimeSpan_Factory.create(
                start=start,
                duration=self.duration,
            )
        return NON_EXISTENT_TIME_SPAN

    # get_current_or_next {{{

    # overloads {{{

    @overload
    def get_current_or_next(
        self,
        moment: datetime,
        *,
        return_is_current: Literal[False],
    ) -> Union[Instrumented_StaticTimeSpan_ABC, NonExistentTimeSpan]:
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
            NonExistentTimeSpan,
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
            NonExistentTimeSpan,
        ],
        Tuple[
            Union[
                Instrumented_StaticTimeSpan_ABC,
                NonExistentTimeSpan,
            ],
            Optional[bool],
        ],
    ]:
        span = self.get_current(moment)
        if not isinstance(span, NonExistentTimeSpan):
            return (span, True) if return_is_current else span

        span = self.get_next(moment)
        if not isinstance(span, NonExistentTimeSpan):
            return (span, False) if return_is_current else span

        span = NON_EXISTENT_TIME_SPAN
        return (span, None) if return_is_current else span

    # }}} get_current_or_next


class PeriodicTimeSpanWithExtraConditions(PeriodicTimeSpan):

    DEFAULT_EXTRA_CONDITIONS_MAX_FAILS = 20

    def __init__(
        self,
        period_engine: PeriodicTimePoint_ABC,
        duration: seconds,
        extra_conditions: Iterable[
            Callable[[Instrumented_StaticTimeSpan_ABC], bool]
        ] = None,
        extra_conditions_any: bool = False,
    ):
        super().__init__(period_engine, duration)
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
        NonExistentTimeSpan,
    ]:
        span = super().get_current(moment)
        if not isinstance(span, NonExistentTimeSpan) and self.extra_conditions_ok(span):
            return span
        return NON_EXISTENT_TIME_SPAN

    def get_next(
        self,
        moment: datetime,
        extra_conditions_max_fails: Union[
            Literal[ExtraConditionsMaxFails.NOT_SPECIFIED],
            int,
            None,
        ] = ExtraConditionsMaxFails.NOT_SPECIFIED,
    ) -> Union[
        Instrumented_StaticTimeSpan_ABC,
        NonExistentTimeSpan,
    ]:
        if extra_conditions_max_fails is ExtraConditionsMaxFails.NOT_SPECIFIED:
            extra_conditions_max_fails = self.DEFAULT_EXTRA_CONDITIONS_MAX_FAILS

        span = Instrumented_StaticTimeSpan_Factory.create(start=moment, duration=0)
        while True:
            span = super().get_next(span.start)  # type: ignore
            if not isinstance(span, NonExistentTimeSpan):
                if not self.extra_conditions_ok(span):
                    if extra_conditions_max_fails is not None:
                        extra_conditions_max_fails -= 1
                        if extra_conditions_max_fails <= 0:
                            return NON_EXISTENT_TIME_SPAN
                    else:
                        continue
                else:
                    break
            else:
                break

        return span
