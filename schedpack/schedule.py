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
from .static_activity import (
    StaticActivity,
)


class ManualSchedule:
    def __init__(self, activities: Iterable[PeriodicActivity_ABC]):
        self.activities = tuple(activities)

    def get_current(
        self,
        moment: datetime,
    ) -> Tuple[StaticActivity, ...]:
        return tuple(
            StaticActivity(
                payload=activity.payload,
                start=span.start,
                end=span.end,
            )
            for activity, span
            in self._activity__current__s(moment)
            if not isinstance(span, NonExistentTimeSpan)
        )

    def _activity__current__s(
        self,
        moment: datetime,
    ) -> Iterable[
        Tuple[
            PeriodicActivity_ABC,
            Union[Instrumented_StaticTimeSpan_ABC, NonExistentTimeSpan],
        ],
    ]:
        """Return ``((<activity>, <current time span>), ...)``"""
        return map(
            lambda a: (a, a.get_current(moment)),
            self.activities,
        )

    def get_next(
        self,
        moment: datetime,
    ) -> Tuple[StaticActivity, ...]:
        activity__next__s = tuple(self._activity__next__s(moment))
        if not activity__next__s:
            return ()
        soonest_span = min(map(lambda an: an[1], activity__next__s))
        if isinstance(soonest_span, NonExistentTimeSpan):
            return ()
        return tuple(
            StaticActivity(
                payload=activity.payload,
                start=span.start,
                end=span.end,
            )
            for activity, span
            in activity__next__s
            if (
                not isinstance(span, NonExistentTimeSpan)
                and span.start == soonest_span.start
            )
        )

    def _activity__next__s(
        self,
        moment: datetime,
    ) -> Iterable[
        Tuple[
            PeriodicActivity_ABC,
            Union[Instrumented_StaticTimeSpan_ABC, NonExistentTimeSpan],
        ],
    ]:
        """Return ``((<activity>, <next time span>), ...)``"""
        return map(
            lambda a: (a, a.get_next(moment)),
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
    ) -> Tuple[StaticActivity, ...]:
        ...

    @overload
    def get_current_or_next(
        self,
        moment: datetime,
        *,
        return_is_current: Literal[True],
    ) -> Tuple[Tuple[StaticActivity, ...], Optional[bool]]:
        ...

    # }}} overloads

    def get_current_or_next(
        self,
        moment: datetime,
        *,
        return_is_current: bool = False,
    ) -> Union[
        Tuple[StaticActivity, ...],
        Tuple[Tuple[StaticActivity, ...], Optional[bool]],
    ]:
        activities = self.get_current(moment)
        if activities:
            return (activities, True) if return_is_current else activities

        activities = self.get_next(moment)
        if activities:
            return (activities, False) if return_is_current else activities

        return ((), None) if return_is_current else ()

    # }}} get_current_or_next
