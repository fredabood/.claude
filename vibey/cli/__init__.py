"""CLI module for Vibey framework."""

# Lazy import to avoid RuntimeWarning when running with python -m
# The warning occurs because importing 'cli' here causes vibey.cli.main
# to be added to sys.modules before runpy executes it as __main__
def __getattr__(name):
    if name == "cli":
        from vibey.cli.main import cli
        return cli
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["cli"]
