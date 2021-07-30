from datetime import datetime, timedelta
import time

import arrow

from schedpack import (
    CronIterWrapper,
    PeriodicActivityWithExtraConditions,
    ManualSchedule,
)
from schedpack.abc import (
    TimeSpanABC,
)


def cron(day_of_week, hour_minute):
    return f'{hour_minute[1]} {hour_minute[0]} * * {day_of_week}'

# hour, minute
c1 = (8, 0)
c2 = (9, 50)
c3 = (11, 40)

CLASS_DURATION = 5700  # seconds   (2*45 + 5 minutes)


class SchoolClass(PeriodicActivityWithExtraConditions):
    def __init__(
        self, payload, start_cron, extra_conditions=None
    ):
        super().__init__(
            payload, CronIterWrapper(start_cron), CLASS_DURATION,
            extra_conditions=extra_conditions, extra_conditions_any=True
        )



# assumed_now = arrow.now('Europe/Moscow').datetime
assumed_now = arrow.get('2021-07-19T08:35:00', tzinfo='Europe/Moscow').datetime

# week number info ############################################################
base_day = arrow.get('2021-07-10', tzinfo='Europe/Moscow')
base_day_week_number = 1  # keep in mind that first week has number 0
week_count = 2
###############################################################################

def get_week_number(
    *, today: datetime, base_day: datetime, base_day_week_number: int,
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


def week_1(span: TimeSpanABC):
    return get_week_number(
        today=span.start_time, base_day=base_day, base_day_week_number=base_day_week_number,
        week_count=week_count
    ) == 0

def week_2(span: TimeSpanABC):
    return get_week_number(
        today=span.start_time, base_day=base_day, base_day_week_number=base_day_week_number,
        week_count=week_count
    ) == 1



sched = ManualSchedule(
    [
        SchoolClass('fizra', cron('mon,thu', c2)),  # mixed

        SchoolClass('bernadeskij', cron('mon', c1), extra_conditions=[week_2]),
        SchoolClass('smelov_1', cron('mon', c3)),

        SchoolClass('ne_koresh_lk', cron('tue', c1)),
        SchoolClass('zhuk', cron('tue', c2)),
        SchoolClass('smelov_2', cron('tue', c3)),

        SchoolClass('salam_lab', cron('wed', c1), extra_conditions=[week_1]),
        SchoolClass('mops_lab', cron('wed', c1), extra_conditions=[week_2]),
        SchoolClass('mops_lk', cron('wed', c2)),
        SchoolClass('birula_1', cron('wed', c3)),

        SchoolClass('ne_koresh_lab', cron('thu', c1), extra_conditions=[week_2]),
        SchoolClass('bernadeskij', cron('thu', c1), extra_conditions=[week_1]),                    
        SchoolClass('za_shit_ochka_lk (urbanushka)', cron('thu', c3)),

        SchoolClass('ris', cron('fri', c1)),
        SchoolClass('prog_v_inet', cron('fri', c2)),
        SchoolClass('za_shit_ochka_lab', cron('fri', c3)),

        SchoolClass('salam_lk', cron('sat', c2)),
        SchoolClass('ris_lk', cron('sat', c3)),
    ]
)


from pprint import pprint
import time


class stopwatch:
    def __enter__(self):
        self.start = time.perf_counter()

    def __exit__(self, *args, **kwargs):
        self.end = time.perf_counter()
        print('stopwatch: ', self.end - self.start)


with stopwatch():
    res = sched.get_next(assumed_now)
pprint(res)

with stopwatch():
    res = sched.get_current(assumed_now)
pprint(res)

with stopwatch():
    res = sched.get_current_or_next(assumed_now, return_is_current=True)
pprint(res)
