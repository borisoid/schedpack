from datetime import (
    datetime,
    timedelta,
)
import time

import arrow

from schedpack import (
    CronIterWrapper,
    PeriodicActivity_WithExtraConditions,
    ManualSchedule,
)
from schedpack.abstraction.abc import (
    Instrumented_StaticTimeSpan_ABC,
)


def cron(day_of_week, hour_minute):
    return f"{hour_minute[1]} {hour_minute[0]} * * {day_of_week}"


# hour, minute
c1 = (8, 0)
c2 = (9, 50)
c3 = (11, 40)

CLASS_DURATION = 5700  # seconds   (2*45 + 5 minutes)


class SchoolClass(PeriodicActivity_WithExtraConditions):
    def __init__(self, payload, start_cron, extra_conditions=None):
        super().__init__(
            payload,
            CronIterWrapper(start_cron),
            CLASS_DURATION,
            extra_conditions=extra_conditions,
            extra_conditions_any=True,
        )


# assumed_now = arrow.now('Europe/Moscow').datetime
assumed_now = arrow.get("2021-07-19T08:35:00", tzinfo="Europe/Moscow").datetime

# week number info {{{
base_day = arrow.get("2021-07-10", tzinfo="Europe/Moscow")
base_day_week_number = 1  # keep in mind that first week has number 0
week_count = 2
# }}} week number info


def get_week_number(
    *,
    today: datetime,
    base_day: datetime,
    base_day_week_number: int,
    week_count: int,
):
    """
    assuming all weeks are numbered 0 through <week_count-1>
    given a day <base_day> and number of week on this day <base_day_week_number>
    calculate what week number it is on <today>
    """
    first_day_of_base_week = base_day - timedelta(days = base_day.weekday())
    first_day_of_current_week = today - timedelta(days = today.weekday())

    week_count_starting_from_base_week = (
        (first_day_of_current_week - first_day_of_base_week) // 7
    ).days

    return (week_count_starting_from_base_week + base_day_week_number) % week_count


def week_1(span: Instrumented_StaticTimeSpan_ABC):
    return get_week_number(
        today=span.start,
        base_day=base_day,
        base_day_week_number=base_day_week_number,
        week_count=week_count,
    ) == 0


def week_2(span: Instrumented_StaticTimeSpan_ABC):
    return get_week_number(
        today=span.start,
        base_day=base_day,
        base_day_week_number=base_day_week_number,
        week_count=week_count,
    ) == 1


sched = ManualSchedule(
    [
        SchoolClass("mon,thu c2", cron("mon,thu", c2)),  # mixed

        SchoolClass("mon c1 w2", cron("mon", c1), extra_conditions=[week_2]),
        SchoolClass("mon c3", cron("mon", c3)),

        SchoolClass("tue c1", cron("tue", c1)),
        SchoolClass("tue c2", cron("tue", c2)),
        SchoolClass("tue c3", cron("tue", c3)),

        SchoolClass("wed c1 w1", cron("wed", c1), extra_conditions=[week_1]),
        SchoolClass("wed c1 w2", cron("wed", c1), extra_conditions=[week_2]),
        SchoolClass("wed c2", cron("wed", c2)),
        SchoolClass("wed c3", cron("wed", c3)),

        SchoolClass("thu c1 w1", cron("thu", c1), extra_conditions=[week_1]),
        SchoolClass("thu c1 w2", cron("thu", c1), extra_conditions=[week_2]),
        SchoolClass("thu c3", cron("thu", c3)),

        SchoolClass("fri c1", cron("fri", c1)),
        SchoolClass("fri c2", cron("fri", c2)),
        SchoolClass("fri c3", cron("fri", c3)),

        SchoolClass("sat c2", cron("sat", c2)),
        SchoolClass("sat c3", cron("sat", c3)),

        SchoolClass("sun c11", cron("sun", c1)),  # simultaneous
        SchoolClass("sun c12", cron("sun", c1)),
        SchoolClass("sun c2", cron("sun", c2)),
    ]
)


from pprint import pprint
import time


class stopwatch:
    def __enter__(self):
        self.start = time.perf_counter()

    def __exit__(self, *args, **kwargs):
        self.end = time.perf_counter()
        print("stopwatch: ", self.end - self.start)


with stopwatch():
    res = sched.get_next(assumed_now)
pprint(res)

with stopwatch():
    res = sched.get_current(assumed_now)
pprint(res)

with stopwatch():
    res = sched.get_current_or_next(assumed_now, return_is_current=True)
pprint(res)
