"""Module entry point for the Whitfield CLI."""

from whitfield_cli.app import app


def main() -> None:
    """Start the Whitfield CLI command tree.

    Delegates command parsing and process exit handling to Typer.
    """
    app()


if __name__ == "__main__":
    main()
