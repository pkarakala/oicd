"""OICD: Open Interconnect Co-Design, a physics-grounded feasibility engine and product twin."""


def main() -> None:
    """The `oicd` command (see oicd.cli)."""
    from oicd.cli import run

    raise SystemExit(run())
