from datetime import (
    datetime,
    timedelta,
)
from typing import (
    Any,
    Callable,
    Iterable,
    Literal,
    Optional,
    Tuple,
    Union,
    overload,
)

from .abc import (
    Instrumented_StaticTimeSpan_ABC,
    PeriodicActivity_ABC,
    PeriodicTimePoint_ABC,
    PeriodicTimeSpan_ABC,
    StaticTimeSpan_ABC,
    seconds,
)


class TimeSpanInitMixin:

    # __init__ {{{

    # overloads {{{

    @overload
    def __init__(
        self,
        *,
        falsy: bool,
    ):
        ...

    @overload
    def __init__(
        self,
        *,
        start: datetime,
        end: datetime,
    ):
        ...

    @overload
    def __init__(
        self,
        *,
        start: datetime,
        duration: seconds,
    ):
        ...

    @overload
    def __init__(
        self,
        *,
        end: datetime,
        duration: seconds,
    ):
        ...

    # }}} overloads

    def __init__(
        self,
        *,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        duration: Optional[seconds] = None,

        falsy: bool = False,
    ):
        if falsy:
            self.start = None
            self.end = None
            return

        start_nn = start is not None
        end_nn = end is not None
        duration_nn = duration is not None

        _args_count = sum(map(int, (
            start_nn,
            end_nn,
            duration_nn,
        )))
        if _args_count != 2:
            raise ValueError(f"Must specify two of these: start, end, duration")

        self.start = start
        self.end = end
        if start_nn and duration_nn:
            self.end = start + timedelta(seconds=duration)  # type: ignore
        elif end_nn and duration_nn:
            self.start = end - timedelta(seconds=duration)  # type: ignore

    # }}} __init__


class Instrumented_StaticTimeSpan(TimeSpanInitMixin, Instrumented_StaticTimeSpan_ABC):
    def __bool__(self) -> bool:
        return bool(self.start) and bool(self.end)

    def __hash__(self) -> int:
        return hash((self.start, self.end))

    def __eq__(self, other: Any) -> bool:
        return issubclass(other, StaticTimeSpan_ABC) and (
            self.start == other.start and self.end == other.end
        )

    def __lt__(self, other: Instrumented_StaticTimeSpan_ABC) -> bool:
        if not self:
            return False
        if not other:
            return True
        return self.start < other.start  # type: ignore

    def __gt__(self, other: Instrumented_StaticTimeSpan_ABC) -> bool:
        if not self:
            return True
        if not other:
            return False
        return self.start > other.start  # type: ignore


class PeriodicTimeSpan(PeriodicTimeSpan_ABC):
    def __init__(self, period_engine: PeriodicTimePoint_ABC, duration: seconds):
        self.period_engine = period_engine
        self.duration = duration

    def is_ongoing(self, moment: datetime) -> bool:
        return bool(self.get_current(moment))

    def get_current(self, moment: datetime) -> Instrumented_StaticTimeSpan_ABC:
        next = self.period_engine.get_next(moment)
        current = self.period_engine.get_next(moment - timedelta(seconds=self.duration))
        if current and ((not next) or (next > current)):
            return Instrumented_StaticTimeSpan(
                start=current,
                duration=self.duration,
            )
        return Instrumented_StaticTimeSpan(falsy=True)

    def get_next(self, moment: datetime) -> Instrumented_StaticTimeSpan_ABC:
        if start := self.period_engine.get_next(moment):
            return Instrumented_StaticTimeSpan(
                start=start,
                duration=self.duration,
            )
        return Instrumented_StaticTimeSpan(falsy=True)

    # get_current_or_next {{{

    # overloads {{{

    @overload
    def get_current_or_next(
        self,
        moment: datetime,
        *,
        return_is_current: Literal[False],
    ) -> Instrumented_StaticTimeSpan_ABC:
        ...

    @overload
    def get_current_or_next(
        self,
        moment: datetime,
        *,
        return_is_current: Literal[True],
    ) -> Tuple[Instrumented_StaticTimeSpan_ABC, Optional[bool]]:
        ...

    # }}} overloads

    def get_current_or_next(
        self,
        moment: datetime,
        *,
        return_is_current: bool = False,
    ) -> Union[
        Instrumented_StaticTimeSpan_ABC,
        Tuple[Instrumented_StaticTimeSpan_ABC, Optional[bool]],
    ]:
        if span := self.get_current(moment):
            return (span, True) if return_is_current else span

        if span := self.get_next(moment):
            return (span, False) if return_is_current else span

        span = Instrumented_StaticTimeSpan(falsy=True)
        return (span, None) if return_is_current else span

    # }}} get_current_or_next


class PeriodicTimeSpanWithExtraConditions(PeriodicTimeSpan):

    _EXTRA_CONDITIONS_MAX_FAILS_NOT_SPECIFIED = object()
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

    def get_current(self, moment: datetime) -> Instrumented_StaticTimeSpan_ABC:
        span = super().get_current(moment)
        if span and self.extra_conditions_ok(span):
            return span
        return Instrumented_StaticTimeSpan(falsy=True)

    def get_next(
        self,
        moment: datetime,
        extra_conditions_max_fails: Union[int, None] = _EXTRA_CONDITIONS_MAX_FAILS_NOT_SPECIFIED,  # type: ignore
    ) -> Instrumented_StaticTimeSpan_ABC:
        if extra_conditions_max_fails is self._EXTRA_CONDITIONS_MAX_FAILS_NOT_SPECIFIED:
            extra_conditions_max_fails = self.DEFAULT_EXTRA_CONDITIONS_MAX_FAILS

        span = Instrumented_StaticTimeSpan(start=moment, duration=0)
        while True:
            span = super().get_next(span.start)  # type: ignore
            if span:
                if not self.extra_conditions_ok(span):
                    if extra_conditions_max_fails is not None:
                        extra_conditions_max_fails -= 1
                        if extra_conditions_max_fails <= 0:
                            return Instrumented_StaticTimeSpan(falsy=True)
                else:
                    break
            else:
                break

        return span


class PeriodicActivity(PeriodicTimeSpan, PeriodicActivity_ABC):
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


class ResolvedActivity(StaticTimeSpan_ABC):
    """An activity with known start/end time
    """

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
        return f"{self.__class__.__name__}(payload={self.payload!r}, start=<{self.start!s}>, end=<{self.end!s}>)"


class ManualSchedule:
    def __init__(self, activities: Iterable[PeriodicActivity_ABC]):
        self.activities = tuple(activities)

    def get_next(
        self,
        moment: datetime,
    ) -> Tuple[ResolvedActivity, ...]:
        activity__next__s = self._activity__next__s(moment)
        if not activity__next__s:
            return ()
        soonest_span = min(map(lambda an: an[1], activity__next__s))
        return () if not soonest_span else tuple(
            ResolvedActivity(activity.payload, start=span.start, end=span.end)  # type: ignore
            for activity, span
            in activity__next__s
            if span.start == soonest_span.start
        )

    def _activity__next__s(
        self,
        moment: datetime,
    ) -> Tuple[
        Tuple[PeriodicActivity_ABC, Instrumented_StaticTimeSpan_ABC],
        ...,
    ]:
        """Return ``((<activity>, <next time span>), ...)``
        """
        return tuple(map(
            lambda a: (a, a.get_next(moment)),
            self.activities,
        ))

    def get_current(
        self,
        moment: datetime,
    ) -> Tuple[ResolvedActivity, ...]:
        activity__current__s = self._activity__current__s(moment)
        return tuple(
            ResolvedActivity(activity.payload, start=span.start, end=span.end)  # type: ignore
            for activity, span
            in activity__current__s
            if span  # if is current
        )

    def _activity__current__s(
        self,
        moment: datetime,
    ) -> Tuple[
        Tuple[PeriodicActivity_ABC, Instrumented_StaticTimeSpan_ABC],
        ...,
    ]:
        """Return ``((<activity>, <current time span>), ...)``
        """
        return tuple(map(
            lambda a: (a, a.get_current(moment)),
            self.activities,
        ))

    # get_current_or_next {{{

    # overloads {{{

    @overload
    def get_current_or_next(
        self,
        moment: datetime,
        *,
        return_is_current: Literal[False],
    ) -> Tuple[ResolvedActivity, ...]:
        ...

    @overload
    def get_current_or_next(
        self,
        moment: datetime,
        *,
        return_is_current: Literal[True],
    ) -> Tuple[Tuple[ResolvedActivity, ...], Optional[bool]]:
        ...

    # }}} overloads

    def get_current_or_next(
        self,
        moment: datetime,
        *,
        return_is_current: bool = False,
    ) -> Union[
        Tuple[ResolvedActivity, ...],
        Tuple[Tuple[ResolvedActivity, ...], Optional[bool]],
    ]:
        activity__current_or_next__ongoing__s = (
            self._activity__current_or_next__ongoing__s(moment)
        )
        if not activity__current_or_next__ongoing__s:
            return ((), None) if return_is_current else ()

        current_s = tuple(
            ResolvedActivity(activity.payload, start=span.start, end=span.end)  # type: ignore
            for activity, span, ongoing
            in activity__current_or_next__ongoing__s
            if ongoing
        )
        if current_s:
            return (current_s, True) if return_is_current else current_s

        soonest_span = min(map(
            lambda acono: acono[1],
            activity__current_or_next__ongoing__s,
        ))
        next_s = tuple(
            ResolvedActivity(activity.payload, start=span.start, end=span.end)  # type: ignore
            for activity, span, ongoing
            in activity__current_or_next__ongoing__s
            if ongoing == False and span.start == soonest_span.start
        )
        if next_s:
            return (next_s, False) if return_is_current else next_s

        return ((), None) if return_is_current else ()

    # }}} get_current_or_next

    def _activity__current_or_next__ongoing__s(
        self,
        moment: datetime,
    ) -> Tuple[
        Tuple[
            PeriodicActivity_ABC,
            Instrumented_StaticTimeSpan_ABC,
            Optional[bool]
        ],
        ...,
    ]:
        """Return ``((<activity>, <current or next time span>, <is it ongoing>), ...)``
        """

        def mapper(
            activity: PeriodicActivity_ABC,
        ) -> Tuple[
            PeriodicActivity_ABC,
            Instrumented_StaticTimeSpan_ABC,
            Optional[bool],
        ]:
            span, ongoing = activity.get_current_or_next(moment, return_is_current=True)
            return (activity, span, ongoing)

        return tuple(map(mapper, self.activities))
