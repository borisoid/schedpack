from datetime import (
    datetime,
    timedelta,
)
from typing import (
    Any,
    Callable,
    Iterable,
    Optional,
    Tuple,
    Union,
)

from .abc import (
    seconds,
    Instrumented_StaticTimeSpanABC,
    StaticTimeSpanABC,
    PeriodicTimePointABC,
    PeriodicTimeSpanABC,
    PeriodicActivityABC,
)


class TimeSpanInitMixin:
    def __init__(
        self,
        *,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        duration: Optional[seconds] = None,
    ):
        start_nn = start is not None
        end_nn = end is not None
        duration_nn = duration is not None

        if start_nn and end_nn and duration_nn:
            raise ValueError('Cannot specify all three: start, end, duration')

        self.start = start
        self.end = end
        if start_nn and duration_nn:
            self.end = start + timedelta(seconds=duration)
        elif end_nn and duration_nn:
            self.start = end - timedelta(seconds=duration)


class Instrumented_StaticTimeSpan(TimeSpanInitMixin, Instrumented_StaticTimeSpanABC):
    def __bool__(self) -> bool:
        return bool(self.start) and bool(self.end)

    def __hash__(self) -> int:
        return hash((self.start, self.end))
    
    def __eq__(self, other: Any) -> bool:
        return issubclass(other, StaticTimeSpanABC) and (
            self.start == other.start and
            self.end == other.end
        )

    def __lt__(self, other: StaticTimeSpanABC) -> bool:
        self_start, other_start = self.start, other.start
        return not other_start or (self_start and self_start < other_start)

    def __gt__(self, other: StaticTimeSpanABC) -> bool:
        self_start, other_start = self.start, other.start
        return not self_start or (other_start and other_start < self_start)


class PeriodicTimeSpan(PeriodicTimeSpanABC):
    def __init__(self, period_engine: PeriodicTimePointABC, duration: seconds):
        self.period_engine = period_engine
        self.duration = duration

    def is_ongoing(self, moment: datetime) -> bool:
        return bool(self.get_current(moment))

    def get_current(self, moment: datetime) -> Instrumented_StaticTimeSpanABC:
        next = self.period_engine.get_next(moment)
        current = self.period_engine.get_next(moment - timedelta(seconds=self.duration))
        if (not next) or (current and (next > current)):
            return Instrumented_StaticTimeSpan(start=current, duration=self.duration)
        else:
            return Instrumented_StaticTimeSpan()

    def get_next(self, moment: datetime) -> Instrumented_StaticTimeSpanABC:
        return Instrumented_StaticTimeSpan(
            start=self.period_engine.get_next(moment),
            duration=self.duration,
        )

    def get_current_or_next(
        self, moment: datetime, *, return_is_current: bool = False
    ) -> Union[Instrumented_StaticTimeSpanABC, Tuple[Instrumented_StaticTimeSpanABC, Optional[bool]]]:
        if span := self.get_current(moment):
            return (span, True) if return_is_current else span

        if span := self.get_next(moment):
            return (span, False) if return_is_current else span

        span = Instrumented_StaticTimeSpan()
        return (span, None) if return_is_current else span


class PeriodicTimeSpanWithExtraConditions(PeriodicTimeSpan):
    def __init__(
        self,
        period_engine: PeriodicTimePointABC,
        duration: seconds,
        extra_conditions: Iterable[Callable[[Instrumented_StaticTimeSpanABC], bool]] = None,
        extra_conditions_any: bool = False,
    ):
        super().__init__(period_engine, duration)
        self.extra_conditions = extra_conditions
        self.extra_conditions_any = extra_conditions_any

    def extra_conditions_ok(
        self, span: Instrumented_StaticTimeSpanABC
    ) -> bool:
        if not self.extra_conditions:
            return True

        return (
            any(map(lambda ec: ec(span), self.extra_conditions))
            if self.extra_conditions_any else
            all(map(lambda ec: ec(span), self.extra_conditions))
        )

    def get_current(self, moment: datetime) -> Instrumented_StaticTimeSpanABC:
        span = super().get_current(moment)
        if span and self.extra_conditions_ok(span):
            return span
        else:
            return Instrumented_StaticTimeSpan()

    def get_next(
        self, moment: datetime, extra_conditions_max_fails=20
    ) -> Instrumented_StaticTimeSpanABC:
        span = Instrumented_StaticTimeSpan(start=moment, duration=0)
        while True:
            span = super().get_next(span.start)
            if span:
                if not self.extra_conditions_ok(span):
                    if extra_conditions_max_fails is not None:
                        extra_conditions_max_fails -= 1
                        if extra_conditions_max_fails <= 0:
                            return Instrumented_StaticTimeSpan()
                else:
                    break
            else:
                break

        return span


class PeriodicActivity(PeriodicTimeSpan, PeriodicActivityABC):
    def __init__(
        self,
        payload: Any,
        period_engine: PeriodicTimePointABC,
        duration: seconds,
    ):
        super().__init__(period_engine, duration)
        self.payload = payload


class PeriodicActivityWithExtraConditions(PeriodicTimeSpanWithExtraConditions, PeriodicActivityABC):
    def __init__(
        self,
        payload: Any,
        period_engine: PeriodicTimePointABC,
        duration: seconds,
        extra_conditions: Iterable[Callable[[Instrumented_StaticTimeSpanABC], bool]] = None,
        extra_conditions_any: bool = False,
    ):
        super().__init__(period_engine, duration, extra_conditions, extra_conditions_any)
        self.payload = payload


class ResolvedActivity(StaticTimeSpanABC):
    """An activity with known start/end time"""

    def __init__(self, payload: Any, start: datetime, end: datetime):
        self.payload = payload
        self.start = start
        self.end = end

    def __repr__(self):
        return f'<{self.payload!s}: [{self.start!s} ... {self.end!s}]>'


class ManualSchedule:
    def __init__(self, activities: Iterable[PeriodicActivityABC]):
        self.activities = tuple(activities)

    def get_next(self, moment: datetime) -> Tuple[ResolvedActivity]:
        activity__next__s = self._activity__next__s(moment)
        if not activity__next__s:
            return ()
        soonest_span = min(map(lambda an: an[1], activity__next__s))
        return () if not soonest_span else tuple(
            ResolvedActivity(activity.payload, span.start, span.end)
            for activity, span in activity__next__s
            if span.start == soonest_span.start
        )

    def _activity__next__s(
        self, moment: datetime
    ) -> Tuple[Tuple[PeriodicActivityABC, Instrumented_StaticTimeSpanABC]]:
        """Return ``((<activity>, <next time span>), ...)``"""
        return tuple(map(
            lambda a: (a, a.get_next(moment)),
            self.activities
        ))

    def get_current(self, moment: datetime) -> Tuple[ResolvedActivity]:
        activity__current__s = self._activity__current__s(moment)
        return tuple(
            ResolvedActivity(activity.payload, span.start, span.end)
            for activity, span in activity__current__s
            if span  # if is current
        )

    def _activity__current__s(
        self, moment: datetime
    ) -> Tuple[Tuple[PeriodicActivityABC, Instrumented_StaticTimeSpanABC]]:
        """Return ``((<activity>, <current time span>), ...)``"""
        return tuple(map(
            lambda a: (a, a.get_current(moment)),
            self.activities
        ))

    def get_current_or_next(
        self, moment: datetime, *, return_is_current: bool = False
    ) -> Union[Tuple[ResolvedActivity], Tuple[Tuple[ResolvedActivity], bool]]:
        activity__current_or_next__ongoing__s = self._activity__current_or_next__ongoing__s(moment)
        if not activity__current_or_next__ongoing__s:
            return ((), None) if return_is_current else ()
        
        current_s = tuple(
            ResolvedActivity(activity.payload, span.start, span.end)
            for activity, span, ongoing in activity__current_or_next__ongoing__s
            if ongoing
        )
        if current_s:
            return (current_s, True) if return_is_current else current_s

        soonest_span = min(map(lambda acono: acono[1], activity__current_or_next__ongoing__s))
        next_s = tuple(
            ResolvedActivity(activity.payload, span.start, span.end)
            for activity, span, ongoing in activity__current_or_next__ongoing__s
            if ongoing == False and span.start == soonest_span.start
        )
        if next_s:
            return (next_s, False) if return_is_current else next_s

        return ((), None) if return_is_current else ()

    def _activity__current_or_next__ongoing__s(
        self, moment: datetime
    ) -> Tuple[Tuple[PeriodicActivityABC, Instrumented_StaticTimeSpanABC, bool]]:
        """Return ``((<activity>, <current or next time span>, <is it ongoing>), ...)``"""
        def mapper(activity: PeriodicActivityABC):
            span, ongoing = activity.get_current_or_next(moment, return_is_current=True)
            return (activity, span, ongoing)
        return tuple(map(mapper, self.activities))
