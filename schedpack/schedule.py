from datetime import (
    datetime,
)
from typing import (
    Iterable,
    Literal,
    Optional,
    Tuple,
    Union,
    overload,
)

from .abstraction.abc import (
    Instrumented_StaticTimeSpan_ABC,
    PeriodicActivity_ABC,
)
from .abstraction.non_existent_time_span import (
    NonExistentTimeSpan,
)
from .resolved_activity import (
    ResolvedActivity,
)


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
        if isinstance(soonest_span, NonExistentTimeSpan):
            return ()
        return tuple(
            ResolvedActivity(activity.payload, start=span.start, end=span.end)
            for activity, span
            in activity__next__s
            if not isinstance(span, NonExistentTimeSpan) and span.start == soonest_span.start
        )

    def _activity__next__s(
        self,
        moment: datetime,
    ) -> Iterable[Tuple[PeriodicActivity_ABC, Union[Instrumented_StaticTimeSpan_ABC, NonExistentTimeSpan]]]:
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
            ResolvedActivity(activity.payload, start=span.start, end=span.end)
            for activity, span
            in self._activity__current__s(moment)
            if not isinstance(span, NonExistentTimeSpan)
        )

    def _activity__current__s(
        self,
        moment: datetime,
    ) -> Iterable[Tuple[PeriodicActivity_ABC, Union[Instrumented_StaticTimeSpan_ABC, NonExistentTimeSpan]]]:
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
            ResolvedActivity(activity.payload, start=span.start, end=span.end)
            for activity, span, ongoing
            in activity__current_or_next__ongoing__s
            if ongoing and not isinstance(span, NonExistentTimeSpan)  # "not isinstance" check is solely for typing
        )
        if current_s:
            return (current_s, True) if return_is_current else current_s

        soonest_span = min(map(
            lambda acono: acono[1],
            activity__current_or_next__ongoing__s,
        ))
        if isinstance(soonest_span, NonExistentTimeSpan):
            return ((), None) if return_is_current else ()

        next_s = tuple(
            ResolvedActivity(activity.payload, start=span.start, end=span.end)
            for activity, span, ongoing
            in activity__current_or_next__ongoing__s
            if (
                ongoing is False
                and not isinstance(span, NonExistentTimeSpan)
                and span.start == soonest_span.start
            )
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
            Union[Instrumented_StaticTimeSpan_ABC, NonExistentTimeSpan],
            Optional[bool],
        ],
    ]:
        """Return ``((<activity>, <current or next time span>, <is it ongoing>), ...)``"""

        def mapper(
            activity: PeriodicActivity_ABC,
        ) -> Tuple[
            PeriodicActivity_ABC,
            Union[Instrumented_StaticTimeSpan_ABC, NonExistentTimeSpan],
            Optional[bool],
        ]:
            span, ongoing = activity.get_current_or_next(moment, return_is_current=True)
            return (activity, span, ongoing)

        return map(mapper, self.activities)
