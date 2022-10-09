from typing import (
    TYPE_CHECKING,
    Union,
)

if TYPE_CHECKING:
    from .abc import Instrumented_StaticTimeSpan_ABC


class NonExistentTimeSpanMeta(type):
    pass
  

class NonExistentTimeSpan(metaclass=NonExistentTimeSpanMeta):
    def __init_subclass__(cls) -> None:
        raise NotImplementedError("SEALED CLASS")

    def __lt__(
        self,
        other: Union[
            "Instrumented_StaticTimeSpan_ABC",
            "NonExistentTimeSpan",
        ],
    ) -> bool:
        """``NonExistentTimeSpan`` is considered to be
        infinitely far in the future,
        so it must never be less than any other one
        """
        return False

    def __gt__(
        self,
        other: Union[
            "Instrumented_StaticTimeSpan_ABC",
            "NonExistentTimeSpan",
        ],
    ) -> bool:
        """``NonExistentTimeSpan`` is considered to be
        infinitely far in the future,
        so it must alway be greater than any other one
        """
        return True


NON_EXISTENT_TIME_SPAN = NonExistentTimeSpan()

# singleton (good enough)
NonExistentTimeSpanMeta.__call__ = lambda cls: NON_EXISTENT_TIME_SPAN  # type: ignore
