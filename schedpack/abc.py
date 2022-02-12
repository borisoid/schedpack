from abc import (
    ABC,
    abstractmethod,
)
from datetime import (
    datetime,
)
from typing import (
    Any,
    Optional,
    Tuple,
    Union,
)


seconds = float


class StaticTimeSpanABC(ABC):
    start: Optional[datetime] = None
    end: Optional[datetime] = None

    @classmethod
    def __subclasshook__(cls, subclass):
        return (
            hasattr(subclass, 'start') and
            hasattr(subclass, 'end')
        )

    def __str__(self):
        return f'[{self.start!s} ... {self.end!s}]'


class Instrumented_StaticTimeSpanABC(StaticTimeSpanABC):
    @abstractmethod
    def __bool__(self) -> bool:
        pass
    
    @abstractmethod
    def __hash__(self) -> int:
        pass

    @abstractmethod
    def __eq__(self, other: Any) -> bool:
        pass

    @abstractmethod
    def __lt__(self, other: StaticTimeSpanABC) -> bool:
        """TimeSpan with no start is considered to be
        infinitely far in the future, so it's never less than any other one
        """

    @abstractmethod
    def __gt__(self, other: StaticTimeSpanABC) -> bool:
        """TimeSpan with no start is considered to be
        infinitely far in the future, so it's always greater than any other one
        """


class PeriodicTimePointABC(ABC):
    @abstractmethod
    def get_next(self, moment: datetime) -> Optional[datetime]:
        """Return value must be greater than ``moment``"""


class PeriodicTimeSpanABC(ABC):
    @abstractmethod
    def is_ongoing(self, moment: datetime) -> bool:
        pass

    @abstractmethod
    def get_current(self, moment: datetime) -> Instrumented_StaticTimeSpanABC:
        """Returns TimeSpan that either contains ``moment`` or is falsy"""

    @abstractmethod
    def get_next(self, moment: datetime) -> Instrumented_StaticTimeSpanABC:
        """Returns the earliest TimeSpan that starts after ``moment``;
        Returned TimeSpan may be falsy if there is no next period;
        Return value start time must be greater than ``moment``
        """

    @abstractmethod
    def get_current_or_next(
        self, moment: datetime, *, return_is_current: bool = False
    ) -> Union[Instrumented_StaticTimeSpanABC, Tuple[Instrumented_StaticTimeSpanABC, Optional[bool]]]:
        """Tries to return TimeSpan that contains ``moment``;
        If that is falsy (which means there is no ongoing period),
        returns the earliest TimeSpan that starts after ``moment`` which may be falsy too;
        Falsy TimeSpan return value means there is no next period as well
        """


class PeriodicActivityABC(PeriodicTimeSpanABC):
    payload: Any = None
