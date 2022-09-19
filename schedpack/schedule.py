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

        result = Instrumented_StaticTimeSpan()

        result.start = start
        result.end = end
        if start_nn and duration_nn:
            result.end = start + timedelta(seconds=duration)  # type: ignore
        elif end_nn and duration_nn:
            result.start = end - timedelta(seconds=duration)  # type: ignore

        return result

    # }}} create

    @classmethod
    def create_undefined(cls) -> Instrumented_StaticTimeSpan_ABC:
        return Instrumented_StaticTimeSpan()


class Instrumented_StaticTimeSpan(Instrumented_StaticTimeSpan_ABC):
    def defined(self) -> bool:
        return bool(self.start) and bool(self.end)

    def __hash__(self) -> int:
        return hash((self.start, self.end))

    def __eq__(self, other: Any) -> bool:
        return issubclass(other, StaticTimeSpan_ABC) and (
            self.start == other.start and self.end == other.end
        )

    def __lt__(self, other: Instrumented_StaticTimeSpan_ABC) -> bool:
        if not self.defined():
            return False
        if not other.defined():
            return True
        return self.start < other.start  # type: ignore

    def __gt__(self, other: Instrumented_StaticTimeSpan_ABC) -> bool:
        if not self.defined():
            return True
        if not other.defined():
            return False
        return self.start > other.start  # type: ignore


class PeriodicTimeSpan(PeriodicTimeSpan_ABC):
    def __init__(self, period_engine: PeriodicTimePoint_ABC, duration: seconds):
        self.period_engine = period_engine
        self.duration = duration

    def is_ongoing(self, moment: datetime) -> bool:
        return self.get_current(moment).defined()

    def get_current(self, moment: datetime) -> Instrumented_StaticTimeSpan_ABC:
        next = self.period_engine.get_next(moment)
        current = self.period_engine.get_next(moment - timedelta(seconds=self.duration))
        if current and ((not next) or (next > current)):
            return Instrumented_StaticTimeSpan_Factory.create(
                start=current,
                duration=self.duration,
            )
        return Instrumented_StaticTimeSpan_Factory.create_undefined()

    def get_next(self, moment: datetime) -> Instrumented_StaticTimeSpan_ABC:
        if start := self.period_engine.get_next(moment):
            return Instrumented_StaticTimeSpan_Factory.create(
                start=start,
                duration=self.duration,
            )
        return Instrumented_StaticTimeSpan_Factory.create_undefined()

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
        span = self.get_current(moment)
        if span.defined():
            return (span, True) if return_is_current else span

        span = self.get_next(moment)
        if span.defined():
            return (span, False) if return_is_current else span

        span = Instrumented_StaticTimeSpan_Factory.create_undefined()
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
            if self.extra_conditions_any
            else all(map(lambda ec: ec(span), self.extra_conditions))
        )

    def get_current(self, moment: datetime) -> Instrumented_StaticTimeSpan_ABC:
        span = super().get_current(moment)
        if span.defined() and self.extra_conditions_ok(span):
            return span
        return Instrumented_StaticTimeSpan_Factory.create_undefined()

    def get_next(
        self,
        moment: datetime,
        extra_conditions_max_fails: Union[int, None] = _EXTRA_CONDITIONS_MAX_FAILS_NOT_SPECIFIED,  # type: ignore
    ) -> Instrumented_StaticTimeSpan_ABC:
        if extra_conditions_max_fails is self._EXTRA_CONDITIONS_MAX_FAILS_NOT_SPECIFIED:
            extra_conditions_max_fails = self.DEFAULT_EXTRA_CONDITIONS_MAX_FAILS

        span = Instrumented_StaticTimeSpan_Factory.create(start=moment, duration=0)
        while True:
            span = super().get_next(span.start)  # type: ignore
            if span.defined():
                if not self.extra_conditions_ok(span):
                    if extra_conditions_max_fails is not None:
                        extra_conditions_max_fails -= 1
                        if extra_conditions_max_fails <= 0:
                            return Instrumented_StaticTimeSpan_Factory.create_undefined()
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
        return f"{self.__class__.__name__}(payload={self.payload!r}, start=<{self.start!s}>, end=<{self.end!s}>)"


class ManualSchedule:
    def __init__(self, activities: Iterable[PeriodicActivity_ABC]):
        self.activities = tuple(activities)

    def get_next(
        self,
        moment: datetime,
    ) -> Tuple[ResolvedActivity, ...]:
        activity__next__s = tuple(self._activity__next__s(moment))
        if not activity__next__s:
            return ()
        soonest_span = min(map(lambda an: an[1], activity__next__s))
        return () if not soonest_span.defined() else tuple(
            ResolvedActivity(activity.payload, start=span.start, end=span.end)  # type: ignore
            for activity, span
            in activity__next__s
            if span.start == soonest_span.start
        )

    def _activity__next__s(
        self,
        moment: datetime,
    ) -> Iterable[Tuple[PeriodicActivity_ABC, Instrumented_StaticTimeSpan_ABC]]:
        """Return ``((<activity>, <next time span>), ...)``"""
        return map(
            lambda a: (a, a.get_next(moment)),
            self.activities,
        )

    def get_current(
        self,
        moment: datetime,
    ) -> Tuple[ResolvedActivity, ...]:
        return tuple(
            ResolvedActivity(activity.payload, start=span.start, end=span.end)  # type: ignore
            for activity, span
            in self._activity__current__s(moment)
            if span.defined()
        )

    def _activity__current__s(
        self,
        moment: datetime,
    ) -> Iterable[Tuple[PeriodicActivity_ABC, Instrumented_StaticTimeSpan_ABC]]:
        """Return ``((<activity>, <current time span>), ...)``"""
        return map(
            lambda a: (a, a.get_current(moment)),
            self.activities,
        )

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
        activity__current_or_next__ongoing__s = tuple(
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
    ) -> Iterable[
        Tuple[
            PeriodicActivity_ABC,
            Instrumented_StaticTimeSpan_ABC,
            Optional[bool],
        ],
    ]:
        """Return ``((<activity>, <current or next time span>, <is it ongoing>), ...)``"""

        def mapper(
            activity: PeriodicActivity_ABC,
        ) -> Tuple[
            PeriodicActivity_ABC,
            Instrumented_StaticTimeSpan_ABC,
            Optional[bool],
        ]:
            span, ongoing = activity.get_current_or_next(moment, return_is_current=True)
            return (activity, span, ongoing)

        return map(mapper, self.activities)
