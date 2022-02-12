# Schedpack

This is a slightly modified version of scheduler that i wrote and used for
my auto-microsoft-teams-class-attender bot during 2020 lockdown

## Usage example

A little set up

```python
import calendar
from datetime import date, datetime

import arrow

from schedpack import (
    CronIterWrapper,
    PeriodicActivityWithExtraConditions,
)
from schedpack.abc import (
    Instrumented_StaticTimeSpanABC,
    PeriodicTimePointABC,
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
            payload,
            CronIterWrapper(start_cron),
            CLASS_DURATION,
            extra_conditions=extra_conditions,
            extra_conditions_any=True
        )

def get_week_number_in_month(date_: date):
    cal = calendar.monthcalendar(date_.year, date_.month)
    for i, week in enumerate(cal):
        if date_.day in week:
            return i + 1

def odd_week(span: Instrumented_StaticTimeSpanABC):
    return get_week_number_in_month(span.start.date()) % 2 == 1

def even_week(span: Instrumented_StaticTimeSpanABC):
    return get_week_number_in_month(span.start.date()) % 2 == 0
```

```python
schedule = ManualSchedule([
    SchoolClass('mon,thu c2', cron('mon,thu', c2)),  # mixed

    SchoolClass('mon c1 ew', cron('mon', c1), extra_conditions=[even_week]),
    SchoolClass('mon c3', cron('mon', c3)),

    SchoolClass('tue c1', cron('tue', c1)),
    SchoolClass('tue c2', cron('tue', c2)),
    SchoolClass('tue c3', cron('tue', c3)),

    SchoolClass('wed c1 ow', cron('wed', c1), extra_conditions=[odd_week]),
    SchoolClass('wed c1 ew', cron('wed', c1), extra_conditions=[even_week]),
    SchoolClass('wed c2', cron('wed', c2)),
    SchoolClass('wed c3', cron('wed', c3)),

    SchoolClass('thu c1 ow', cron('thu', c1), extra_conditions=[odd_week]),  
    SchoolClass('thu c1 ew', cron('thu', c1), extra_conditions=[even_week]),                  
    SchoolClass('thu c3', cron('thu', c3)),

    SchoolClass('fri c1', cron('fri', c1)),
    SchoolClass('fri c2', cron('fri', c2)),
    SchoolClass('fry c3', cron('fri', c3)),

    SchoolClass('sat c2', cron('sat', c2)),
    SchoolClass('sat c3', cron('sat', c3)),

    SchoolClass('sun c11', cron('sun', c1)),  # simultaneous
    SchoolClass('sun c12', cron('sun', c1)),
    SchoolClass('sun c2', cron('sun', c2)),
])

# jul 2021 calendar
# [[ 0,  0,  0,  1,  2,  3,  4],
#  [ 5,  6,  7,  8,  9, 10, 11],
#  [12, 13, 14, 15, 16, 17, 18],
#  [19, 20, 21, 22, 23, 24, 25],
#  [26, 27, 28, 29, 30, 31,  0]]

moment = arrow.get('2021-07-01T07:30:00', tzinfo='Europe/Moscow').datetime
activities = schedule.get_next(moment)
print(activities)  # (<thu c1 ow: [2021-07-01 08:00:00+03:00 ... 2021-07-01 09:35:00+03:00]>,)

moment = arrow.get('2021-07-01T08:00:00', tzinfo='Europe/Moscow').datetime
activities = schedule.get_current(moment)
print(activities)  # (<thu c1 ow: [2021-07-01 08:00:00+03:00 ... 2021-07-01 09:35:00+03:00]>,)

moment = arrow.get('2021-07-02T09:35:00', tzinfo='Europe/Moscow').datetime
activities = schedule.get_current(moment)
print(activities)  # ()

moment = arrow.get('2021-07-04T08:30:00', tzinfo='Europe/Moscow').datetime
activities = schedule.get_current(moment)
print(activities)
# (
#   <sun c11: [2021-07-04 08:00:00+03:00 ... 2021-07-04 09:35:00+03:00]>,
#   <sun c12: [2021-07-04 08:00:00+03:00 ... 2021-07-04 09:35:00+03:00]>,
# )

moment = arrow.get('2021-07-04T08:30:00', tzinfo='Europe/Moscow').datetime
activities, is_current = schedule.get_current_or_next(
    moment, return_is_current=True
)
print(activities, is_current)
# (
#   <sun c11: [2021-07-04 08:00:00+03:00 ... 2021-07-04 09:35:00+03:00]>,
#   <sun c12: [2021-07-04 08:00:00+03:00 ... 2021-07-04 09:35:00+03:00]>,
# )
# True

moment = arrow.get('2021-07-04T07:30:00', tzinfo='Europe/Moscow').datetime
activities, is_current = schedule.get_current_or_next(
    moment, return_is_current=True
)
print(activities, is_current)
# (
#   <sun c11: [2021-07-04 08:00:00+03:00 ... 2021-07-04 09:35:00+03:00]>,
#   <sun c12: [2021-07-04 08:00:00+03:00 ... 2021-07-04 09:35:00+03:00]>,
# )
# False
```
