"""CBETA CLI - Chinese Buddhist Electronic Text Association API wrapper."""

from .cbeta_cli import main
from .utils.cbeta_backend import CbetaClient, DEFAULT_BASE_URL

__version__ = "2.6.0"
__all__ = ["main", "CbetaClient", "DEFAULT_BASE_URL"]