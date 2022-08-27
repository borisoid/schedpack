import calendar
from datetime import (
    date,
    datetime,
)

from schedpack import (
    CronIterWrapper,
    PeriodicActivityWithExtraConditions,
)
from schedpack.abc import (
    Instrumented_StaticTimeSpan_ABC,
    PeriodicTimePoint_ABC,
)


def cron(day_of_week, hour_minute):
    return f"{hour_minute[1]} {hour_minute[0]} * * {day_of_week}"


# hour, minute
c1 = (8, 0)
c2 = (9, 50)
c3 = (11, 40)

CLASS_DURATION = 5700  # seconds   (2*45 + 5 minutes)


class SchoolClass(PeriodicActivityWithExtraConditions):
    def __init__(self, payload, start_cron, extra_conditions=None):
        super().__init__(
            payload,
            CronIterWrapper(start_cron),
            CLASS_DURATION,
            extra_conditions=extra_conditions,
            extra_conditions_any=True,
        )


def get_week_number_in_month(date_: date):
    cal = calendar.monthcalendar(date_.year, date_.month)
    for i, week in enumerate(cal):
        if date_.day in week:
            return i + 1


def odd_week(span: Instrumented_StaticTimeSpan_ABC):
    return get_week_number_in_month(span.start.date()) % 2 == 1


def even_week(span: Instrumented_StaticTimeSpan_ABC):
    return get_week_number_in_month(span.start.date()) % 2 == 0


def impossible_condition(*args, **kwargs):
    return False


class InfinitelyFarPeriodicTimePoint(PeriodicTimePoint_ABC):
    def get_next(self, moment: datetime):
        return None


class NeverStartingPeriodicActivity(PeriodicActivityWithExtraConditions):
    def __init__(self, payload):
        super().__init__(
            payload,
            InfinitelyFarPeriodicTimePoint(),
            0,
            extra_conditions=(),
            extra_conditions_any=True,
        )
