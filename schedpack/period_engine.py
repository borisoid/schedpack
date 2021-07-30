from datetime import datetime

from croniter import croniter

from .abc import (
    PeriodicTimePointABC
)


class CronIterWrapper(PeriodicTimePointABC):
    def __init__(self, cron_expression: str, *args, **kwargs):
        self.cron = croniter(cron_expression, *args, **kwargs)

    def get_next(self, moment: datetime) -> datetime:
        return self.cron.get_next(start_time=moment, ret_type=datetime)
