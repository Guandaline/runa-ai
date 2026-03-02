# src/nala/athomic/performance/bootstrap.py
import asyncio

from nala.athomic.observability import get_logger

logger = get_logger(__name__)


def install_uvloop_if_available() -> None:
    """
    Attempts to install the highly performant uvloop library as the main
    asyncio event loop policy.

    This function must be called very early in the application's startup
    sequence, before any asynchronous operations begin. It logs the outcome
    for observability.
    """
    try:
        import uvloop

        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        logger.info("uvloop successfully installed as the event loop policy.")
    except ImportError:
        # This is the expected path when uvloop is not installed
        logger.info("uvloop not found. Using the default asyncio event loop.")
    except Exception as e:
        # Catches unexpected errors during policy setting
        logger.warning(f"An error occurred while installing uvloop: {e}")
