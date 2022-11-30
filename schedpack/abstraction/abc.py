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
    Tuple,
    Union,
    overload,
)

from .non_existent_time_span import (
    NonExistentTimeSpanType,
)


class StaticTimeSpan_ABC(ABC):
    start: datetime
    end: datetime

    @classmethod
    def __subclasshook__(cls, subclass) -> bool:
        return hasattr(subclass, "start") and hasattr(subclass, "end")


class Instrumented_StaticTimeSpan_ABC(StaticTimeSpan_ABC):

    @abstractmethod
    def __hash__(self) -> int:
        ...

    @abstractmethod
    def __eq__(self, other: Any) -> bool:
        ...

    @abstractmethod
    def __lt__(
        self,
        other: Union[
            "Instrumented_StaticTimeSpan_ABC",
            NonExistentTimeSpanType,
        ]
    ) -> bool:
        """``NonExistentTimeSpan`` is considered to be
        infinitely far in the future,
        so it must never be less than any other
        ``Instrumented_StaticTimeSpan_ABC`` or ``NonExistentTimeSpan``
        """

    @abstractmethod
    def __gt__(
        self,
        other: Union[
            "Instrumented_StaticTimeSpan_ABC",
            NonExistentTimeSpanType,
        ]) -> bool:
        """``NonExistentTimeSpan`` is considered to be
        infinitely far in the future,
        so it must always be greater than any other
        ``Instrumented_StaticTimeSpan_ABC`` or ``NonExistentTimeSpan``
        """


class PeriodicTimePoint_ABC(ABC):
    @abstractmethod
    def get_next(self, moment: datetime) -> Optional[datetime]:
        """Must return value greater than ``moment`` or ``None``"""


class PeriodicTimeSpan_ABC(ABC):
    @abstractmethod
    def is_ongoing(self, moment: datetime) -> bool:
        ...

    @abstractmethod
    def get_current(
        self,
        moment: datetime,
    ) -> Union[
        Instrumented_StaticTimeSpan_ABC,
        NonExistentTimeSpanType,
    ]:
        """Must return ``Instrumented_StaticTimeSpan_ABC`` that
        contains ``moment``(``[)``);
        If that cannot be found - must return ``NonExistentTimeSpan``;
        """

    @abstractmethod
    def get_next(
        self,
        moment: datetime,
    ) -> Union[
        Instrumented_StaticTimeSpan_ABC,
        NonExistentTimeSpanType,
    ]:
        """Must return the earliest ``Instrumented_StaticTimeSpan_ABC``
        that starts after ``moment``;

        Returned ``Instrumented_StaticTimeSpan_ABC``'s start time
        must be greater than ``moment``;

        Must return ``NonExistentTimeSpan`` if next
        ``Instrumented_StaticTimeSpan_ABC`` cannot be found;
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
    ) -> Union[
        Instrumented_StaticTimeSpan_ABC,
        NonExistentTimeSpanType,
    ]:
        ...

    @overload
    @abstractmethod
    def get_current_or_next(
        self,
        moment: datetime,
        *,
        return_is_current: Literal[True],
    ) -> Tuple[
        Union[
            Instrumented_StaticTimeSpan_ABC,
            NonExistentTimeSpanType,
        ],
        Optional[bool],
    ]:
        ...

    # }}} overloads

    @abstractmethod
    def get_current_or_next(
        self,
        moment: datetime,
        *,
        return_is_current: bool = False,
    ) -> Union[
        Union[
            Instrumented_StaticTimeSpan_ABC,
            NonExistentTimeSpanType,
        ],
        Tuple[
            Union[
                Instrumented_StaticTimeSpan_ABC,
                NonExistentTimeSpanType,
            ],
            Optional[bool],
        ],
    ]:
        """Must return ``Instrumented_StaticTimeSpan_ABC`` that
        contains ``moment``(``[)``);
        If return_is_current==True, must also return ``True``;

        If ``Instrumented_StaticTimeSpan_ABC`` that contains
        ``moment``(``[)``) cannot be found, must return the earliest
        ``Instrumented_StaticTimeSpan_ABC`` that starts after ``moment``;
        If return_is_current==True, must also return ``False``;

        If no ongoing ``Instrumented_StaticTimeSpan_ABC``
        or future ``Instrumented_StaticTimeSpan_ABC`` can be found,
        must return ``NonExistentTimeSpan``;
        If return_is_current==True, must also return ``None``;
        """

    # }}} get_current_or_next


class PeriodicActivity_ABC(PeriodicTimeSpan_ABC):
    payload: Any = None
