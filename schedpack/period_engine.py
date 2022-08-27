from datetime import (
    datetime,
)
from typing import (
    Optional,
)

from croniter import (
    croniter,
)

from .abc import (
    PeriodicTimePoint_ABC,
)


class CronIterWrapper(PeriodicTimePoint_ABC):
    def __init__(self, cron_expression: str, *args, **kwargs):
        self.cron = croniter(cron_expression, *args, **kwargs)

    def get_next(self, moment: datetime) -> Optional[datetime]:
        return self.cron.get_next(start_time=moment, ret_type=datetime)
