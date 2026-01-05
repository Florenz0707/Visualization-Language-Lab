from .events import router as events_router
from .movements import router as movements_router
from .territories import router as territories_router

__all__ = ["events_router", "movements_router", "territories_router"]
