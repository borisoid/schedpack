from typing import (
    Final,
    TYPE_CHECKING,
    Union,
)

if TYPE_CHECKING:
    from .abc import Instrumented_StaticTimeSpan_ABC


class NonExistentTimeSpanMeta(type):
    pass


class NonExistentTimeSpanType(metaclass=NonExistentTimeSpanMeta):
    def __init_subclass__(cls) -> None:
        raise NotImplementedError("SEALED CLASS")

    def __lt__(
        self,
        other: Union[
            "Instrumented_StaticTimeSpan_ABC",
            "NonExistentTimeSpanType",
        ],
    ) -> bool:
        """``NonExistentTimeSpan`` is considered to be
        infinitely far in the future,
        so it must never be less than any other
        ``Instrumented_StaticTimeSpan_ABC`` or ``NonExistentTimeSpan``
        """
        return False

    def __gt__(
        self,
        other: Union[
            "Instrumented_StaticTimeSpan_ABC",
            "NonExistentTimeSpanType",
        ],
    ) -> bool:
        """``NonExistentTimeSpan`` is considered to be
        infinitely far in the future,
        so it must always be greater than any other
        ``Instrumented_StaticTimeSpan_ABC`` or ``NonExistentTimeSpan``
        """
        return True


NonExistentTimeSpan: Final = NonExistentTimeSpanType()

# singleton (good enough)
NonExistentTimeSpanMeta.__call__ = lambda cls: NonExistentTimeSpan  # type: ignore
