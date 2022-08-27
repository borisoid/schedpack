from abc import (
    ABC,
    abstractmethod,
)
from datetime import (
    datetime,
)
from typing import (
    Any,
    Literal,
    Optional,
    overload,
    Tuple,
    Union,
)


seconds = float


class StaticTimeSpan_ABC(ABC):
    start: Optional[datetime] = None
    end: Optional[datetime] = None

    @classmethod
    def __subclasshook__(cls, subclass):
        return hasattr(subclass, "start") and hasattr(subclass, "end")


class Instrumented_StaticTimeSpan_ABC(StaticTimeSpan_ABC):
    @abstractmethod
    def __bool__(self) -> bool:
        ...

    @abstractmethod
    def __hash__(self) -> int:
        ...

    @abstractmethod
    def __eq__(self, other: Any) -> bool:
        ...

    @abstractmethod
    def __lt__(self, other: "Instrumented_StaticTimeSpan_ABC") -> bool:
        """``falsy Instrumented_StaticTimeSpan_ABC`` is considered to be
        infinitely far in the future, so it must never be less than any other one;
        """

    @abstractmethod
    def __gt__(self, other: "Instrumented_StaticTimeSpan_ABC") -> bool:
        """``falsy Instrumented_StaticTimeSpan_ABC`` is considered to be
        infinitely far in the future, so it must alway be greater than any other one;
        """


class PeriodicTimePoint_ABC(ABC):
    @abstractmethod
    def get_next(self, moment: datetime) -> Optional[datetime]:
        """Must return value greater than ``moment`` or None;
        """


class PeriodicTimeSpan_ABC(ABC):
    @abstractmethod
    def is_ongoing(self, moment: datetime) -> bool:
        ...

    @abstractmethod
    def get_current(self, moment: datetime) -> Instrumented_StaticTimeSpan_ABC:
        """Must return ``Instrumented_StaticTimeSpan_ABC`` that
        either contains ``moment``*``[)``* or is falsy;
        """

    @abstractmethod
    def get_next(self, moment: datetime) -> Instrumented_StaticTimeSpan_ABC:
        """Must return the earliest ``Instrumented_StaticTimeSpan_ABC`` that starts after ``moment``;
        Returned ``Instrumented_StaticTimeSpan_ABC``'s start time must be greater than ``moment``;
        Returned ``Instrumented_StaticTimeSpan_ABC`` must be falsy if there is no next ``Instrumented_StaticTimeSpan_ABC``;
        """

    # get_current_or_next {{{

    # overloads {{{

    @overload
    @abstractmethod
    def get_current_or_next(
        self,
        moment: datetime,
        *,
        return_is_current: Literal[False],
    ) -> Instrumented_StaticTimeSpan_ABC:
        ...

    @overload
    @abstractmethod
    def get_current_or_next(
        self,
        moment: datetime,
        *,
        return_is_current: Literal[True],
    ) -> Tuple[Instrumented_StaticTimeSpan_ABC, Optional[bool]]:
        ...

    # }}} overloads

    @abstractmethod
    def get_current_or_next(
        self,
        moment: datetime,
        *,
        return_is_current: bool = False,
    ) -> Union[
        Instrumented_StaticTimeSpan_ABC,
        Tuple[Instrumented_StaticTimeSpan_ABC, Optional[bool]],
    ]:
        """Must return ``Instrumented_StaticTimeSpan_ABC`` that
        contains ``moment``*``[)``*;
        If return_is_current==True, must also return True;

        If ``Instrumented_StaticTimeSpan_ABC`` that contains ``moment``*``[)``* cannot be found,
        must return the earliest ``Instrumented_StaticTimeSpan_ABC`` that starts after ``moment``;
        If return_is_current==True, must also return False;

        If no ongoing ``Instrumented_StaticTimeSpan_ABC``
        or future ``Instrumented_StaticTimeSpan_ABC`` could be found,
        must return ``falsy Instrumented_StaticTimeSpan_ABC``;
        If return_is_current==True, must also return None;
        """

    # }}} get_current_or_next


class PeriodicActivity_ABC(PeriodicTimeSpan_ABC):
    payload: Any = None
