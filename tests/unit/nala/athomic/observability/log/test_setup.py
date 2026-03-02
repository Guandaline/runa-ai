import logging

from loguru import logger

from nala.athomic.observability.log.setup import configure_logging


def test_configure_logging_basic(monkeypatch):
    monkeypatch.setenv("NALA_LOG_LEVEL", "DEBUG")
    configure_logging()
    logger.debug("Test message visible with DEBUG")
    assert logging.getLogger("loguru").level == 0  # DEBUG
