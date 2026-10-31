import sys

from sailrouter.cli.main import main

if __name__ == "__main__":  # worker processes (spawn) re-import this module: do not run the CLI there
    sys.exit(main())
