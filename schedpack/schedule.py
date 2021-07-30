from datetime import (
    datetime,
    timedelta,
)
from typing import (
    Any,
    Callable,
    Iterable,
    Tuple,
    Union,
)

from .abc import (
    seconds,
    TimeSpanABC,
    InnertTimeSpanABC,
    PeriodicTimePointABC,
    PeriodicTimeSpanABC,
    PeriodicActivityABC,
)


class TimeSpanBase(TimeSpanABC):
    def __bool__(self) -> bool:
        return bool(self.start_time) and bool(self.end_time)

    def __eq__(self, other) -> bool:
        return (
            getattr(self, 'start_time') == getattr(other, 'start_time') and
            getattr(self, 'end_time') == getattr(other, 'end_time')
        )

    def __iter__(self):
        return iter((self.start_time, self.end_time))


class TimeSpan(TimeSpanBase):
    def __lt__(self, other):
        # time span with no time is considered to be
        # infinitely far in the future. so it's never less than any other one
        if not self :
            return False
        if not other:
            return True

        self_start = getattr(self, 'start_time')
        other_start = getattr(other, 'start_time')

        return not other_start or (self_start and self_start < other_start)


class TimeSpanByStartTimeAndDuration(TimeSpan):
    def __init__(self, start_time=None, duration=0):
        self.start_time = start_time
        self.end_time = (
            start_time + timedelta(seconds=duration) if start_time else None
        )

    def __str__(self):
        return f'({self.start_time!s} - {self.end_time!s})'

    def __repr__(self):
        return f'({self.start_time!s} - {self.end_time!s})'


class PeriodicTimeSpan(PeriodicTimeSpanABC):
    def __init__(self, period_engine: PeriodicTimePointABC, duration: seconds):
        self.period_engine = period_engine
        self.duration = duration

    def is_ongoing(self, moment: datetime) -> bool:
        return bool(self.get_current(moment))

    def get_current(self, moment: datetime) -> TimeSpanABC:
        next = self.period_engine.get_next(moment)
        current = self.period_engine.get_next(moment - timedelta(seconds=self.duration))
        if (not next) or (current and (next > current)):
            return TimeSpanByStartTimeAndDuration(current, self.duration)
        else:
            return TimeSpanByStartTimeAndDuration()

    def get_next(self, moment: datetime) -> TimeSpanABC:
        return TimeSpanByStartTimeAndDuration(
            self.period_engine.get_next(moment), self.duration
        )

    def get_current_or_next(
        self, moment: datetime, *, return_is_current: bool = False
    ) -> Union[TimeSpanABC, Tuple[TimeSpanABC, Union[bool, None]]]:
        span = self.get_current(moment)
        if span:
            return (span, True) if return_is_current else span

        span = self.get_next(moment)
        if span:
            return (span, False) if return_is_current else span

        span = TimeSpanByStartTimeAndDuration()
        return (span, None) if return_is_current else span


class PeriodicTimeSpanWithExtraConditions(PeriodicTimeSpan):
    def __init__(
        self, period_engine: PeriodicTimePointABC, duration: seconds,
        extra_conditions: Iterable[Callable[[TimeSpanABC], bool]] = None,
        extra_conditions_any: bool = False
    ):
        super().__init__(period_engine, duration)
        self.extra_conditions = extra_conditions
        self.extra_conditions_any = extra_conditions_any

    def extra_conditions_ok(self, span: TimeSpanABC) -> bool:
        if not self.extra_conditions:
            return True

        return (
            any(map(lambda ec: ec(span), self.extra_conditions))
            if self.extra_conditions_any else
            all(map(lambda ec: ec(span), self.extra_conditions))
        )

    def get_current(self, moment: datetime) -> TimeSpanABC:
        span = super().get_current(moment)
        if span and self.extra_conditions_ok(span):
            return span
        else:
            return TimeSpanByStartTimeAndDuration()

    def get_next(self, moment: datetime, extra_conditions_max_fails=20) -> TimeSpanABC:
        span = TimeSpanByStartTimeAndDuration(moment, 0)
        while True:
            span = super().get_next(span.start_time)
            if span:
                if not self.extra_conditions_ok(span):
                    if extra_conditions_max_fails is not None:
                        extra_conditions_max_fails -= 1
                        if extra_conditions_max_fails <= 0:
                            return TimeSpanByStartTimeAndDuration()
                else:
                    break
            else:
                break

        return span


class PeriodicActivity(PeriodicTimeSpan, PeriodicActivityABC):
    def __init__(
        self, payload: Any, period_engine: PeriodicTimePointABC,
        duration: seconds
    ):
        super().__init__(period_engine, duration)
        self.payload = payload


class PeriodicActivityWithExtraConditions(PeriodicTimeSpanWithExtraConditions, PeriodicActivityABC):
    def __init__(
        self, payload: Any, period_engine: PeriodicTimePointABC, duration: seconds,
        extra_conditions: Iterable[Callable[[TimeSpanABC], bool]] = None,
        extra_conditions_any: bool = False
    ):
        super().__init__(period_engine, duration, extra_conditions, extra_conditions_any)
        self.payload = payload


class ResolvedActivity(InnertTimeSpanABC):
    """An activity with known start/end time"""

    def __init__(self, payload: Any, start_time: datetime, end_time: datetime):
        self.payload = payload
        self.start_time = start_time
        self.end_time = end_time

    def __repr__(self):
        return f'{self.payload!s}: {self.start_time!s} - {self.end_time!s}'


class ManualSchedule:
    def __init__(self, activities: Iterable[PeriodicActivityABC]):
        self.activities = activities

    def get_next(self, moment: datetime) -> Tuple[ResolvedActivity]:
        activities_nexts = self.get_activity_next_mapping(moment)
        if not activities_nexts:
            return ()
        soonest_span = min(activities_nexts, key=lambda a: a[1])[1]
        return () if not soonest_span else tuple(
            ResolvedActivity(a[0].payload, *a[1])
            for a in activities_nexts
            if a[1].start_time == soonest_span.start_time
        )

    def get_activity_next_mapping(self, moment: datetime) -> Tuple[Tuple[PeriodicActivityABC, TimeSpanABC]]:
        return tuple(map(
            lambda a: (a, a.get_next(moment)),
            self.activities
        ))

    def get_current(self, moment: datetime) -> Tuple[ResolvedActivity]:
        activities_currents = self.get_activity_current_mapping(moment)
        return tuple(
            ResolvedActivity(a[0].payload, *a[1]) for a in activities_currents if a[1]
        )

    def get_activity_current_mapping(self, moment: datetime) -> Tuple[Tuple[PeriodicActivityABC, TimeSpanABC]]:
        return tuple(map(
            lambda a: (a, a.get_current(moment)),
            self.activities
        ))

    def get_current_or_next(
        self, moment: datetime, *, return_is_current: bool = False
    ) -> Union[Tuple[ResolvedActivity], Tuple[Tuple[ResolvedActivity], bool]]:
        activities_currents_or_nexts = self.get_activity_current_or_next_mapping(moment)
        if not activities_currents_or_nexts:
            return ((), None) if return_is_current else ()
        
        currents = tuple(
            ResolvedActivity(a[0].payload, *a[1])
            for a in activities_currents_or_nexts
            if a[2]  # if is current
        )
        if currents:
            return (currents, True) if return_is_current else currents

        soonest_span = min(activities_currents_or_nexts, key=lambda a: a[1])[1]
        nexts = tuple(
            ResolvedActivity(a[0].payload, *a[1])
            for a in activities_currents_or_nexts
            if a[2] == False and a[1].start_time == soonest_span.start_time
        )
        if nexts:
            return (nexts, False) if return_is_current else nexts

        return ((), None) if return_is_current else ()

    def get_activity_current_or_next_mapping(
        self, moment: datetime
    ) -> Tuple[Tuple[PeriodicActivityABC, TimeSpanABC, bool]]:
        """return ((<activity>, <current or next time span>, <is it ongoing>), ...)"""
        return tuple(map(
            lambda a: (a, *a.get_current_or_next(moment, return_is_current=True)),
            self.activities
        ))
