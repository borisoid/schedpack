from abc import (
    ABC,
    abstractmethod,
)
from datetime import (
    datetime,
)
from typing import (
    Any,
    Tuple,
    Union,
)


seconds = int


class TimeSpanABC(ABC):
    @abstractmethod
    def __init__(self):
        pass

    start_time: datetime = None
    end_time: datetime = None

    @abstractmethod
    def __bool__(self) -> bool:
        pass
    
    @abstractmethod
    def __eq__(self, other: object) -> bool:
        pass

    @abstractmethod
    def __lt__(self, other) -> bool:
        pass

    @abstractmethod
    def __iter__(self):
        """Used for unpacking with * """


class InnertTimeSpanABC(ABC):
    start_time: datetime = None
    end_time: datetime = None


class PeriodicTimePointABC(ABC):
    @abstractmethod
    def get_next(self, moment: datetime) -> Union[datetime, None]:
        """return value must be greater than <moment>"""


class PeriodicTimeSpanABC(ABC):
    @abstractmethod
    def is_ongoing(self, moment: datetime) -> bool:
        pass

    @abstractmethod
    def get_current(self, moment: datetime) -> TimeSpanABC:
        """returns current TimeSpan or falsy TimeSpan"""

    @abstractmethod
    def get_next(self, moment: datetime) -> TimeSpanABC:
        """
        returns next period's TimeSpan or falsy TimeSpan;
        return value start time must be greater than <moment>
        """

    @abstractmethod
    def get_current_or_next(
        self, moment: datetime, *, return_is_current: bool = False
    ) -> Union[TimeSpanABC, Tuple[TimeSpanABC, bool]]:
        """
        returns current TimeSpan;
        if that is falsy returns next period's TimeSpan which may be falsy too
        """


class PeriodicActivityABC(PeriodicTimeSpanABC):
    payload: Any = None
