from .base import Base
from .source import Source
from .update import Update
from .ingest_run import IngestRun

# Ensure analysis models (Report, ReportRun) are registered on the same
# declarative Base so that forward-reference relationships resolve correctly.
try:
    from analysis.models import Report, ReportRun  # noqa: F401
except ImportError:
    pass

__all__ = ["Base", "Source", "Update", "IngestRun"]
