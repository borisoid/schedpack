from typing import (
    TYPE_CHECKING,
    Union,
)

if TYPE_CHECKING:
    from .abc import Instrumented_StaticTimeSpan_ABC


class NonExistentTimeSpan:
    def __init_subclass__(cls) -> None:
        raise NotImplementedError("SEALED CLASS")

    def __lt__(self, other: Union["Instrumented_StaticTimeSpan_ABC", "NonExistentTimeSpan"]) -> bool:
        return False

    def __gt__(self, other: Union["Instrumented_StaticTimeSpan_ABC", "NonExistentTimeSpan"]) -> bool:
        return True


NON_EXISTENT_TIME_SPAN = NonExistentTimeSpan()
