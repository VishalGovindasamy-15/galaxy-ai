"""Allow running Galaxy as a module: python -m galaxy."""

from galaxy.cli.app import main

if __name__ == "__main__":
    main()
