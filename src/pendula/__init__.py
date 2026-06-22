from importlib.metadata import PackageNotFoundError, version

from .cli import main

try:
    __version__ = version("pendula")
except PackageNotFoundError:
    # Fallback for when the package is not installed in the environment yet
    __version__ = "0.0.0-unknown"

__all__ = ["__version__", "main"]
