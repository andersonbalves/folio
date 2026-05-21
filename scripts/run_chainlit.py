"""Chainlit runner script."""

import nest_asyncio

nest_asyncio.apply = lambda *args, **kwargs: None

import sys  # noqa: E402

from chainlit.cli import cli  # noqa: E402

if __name__ == "__main__":
    sys.exit(cli())
