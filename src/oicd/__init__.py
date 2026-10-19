"""OICD: Open Interconnect Co-Design, a feasibility engine with architecture twins."""


def main() -> None:
    """The `oicd` command (see oicd.cli)."""
    from oicd.cli import run

    raise SystemExit(run())
