from __future__ import annotations

import logging


logger = logging.getLogger(
    "vcg"
)


def log_ui_exception(
    error: Exception,
    context: str = "VCG UI operation failed",
) -> None:
    """Log internal failure details without rendering them to the end user."""

    logger.error(
        "%s (%s)",
        context,
        type(
            error
        ).__name__,
        exc_info=True,
    )
