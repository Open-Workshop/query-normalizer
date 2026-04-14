"""CLI tests for query-normalizer."""

from unittest.mock import patch
import pytest


def test_cli_basic_mode():
    from io import StringIO
    import sys

    original_argv = sys.argv
    try:
        sys.argv = ["query-normalizer", "test", "query"]
        with patch("sys.stdout", new_callable=StringIO):
            from query_normalizer.cli import cli

            cli()
    finally:
        sys.argv = original_argv


def test_cli_classic_mode():
    from io import StringIO
    import sys

    original_argv = sys.argv
    try:
        sys.argv = ["query-normalizer", "test", "query", "--mode", "classic"]
        with patch("sys.stdout", new_callable=StringIO):
            from query_normalizer.cli import cli

            cli()
    finally:
        sys.argv = original_argv


def test_cli_embedding_mode():
    from io import StringIO
    import sys

    original_argv = sys.argv
    try:
        sys.argv = ["query-normalizer", "test", "query", "--mode", "embedding"]
        with patch("sys.stdout", new_callable=StringIO):
            from query_normalizer.cli import cli

            cli()
    finally:
        sys.argv = original_argv


def test_cli_both_mode():
    from io import StringIO
    import sys

    original_argv = sys.argv
    try:
        sys.argv = ["query-normalizer", "test", "query", "--mode", "both"]
        with patch("sys.stdout", new_callable=StringIO):
            from query_normalizer.cli import cli

            cli()
    finally:
        sys.argv = original_argv


def test_cli_debug_mode():
    from io import StringIO
    import sys

    original_argv = sys.argv
    try:
        sys.argv = ["query-normalizer", "Это", "ghbdtn", "алфaвиты", "--mode", "both", "--debug"]
        with patch("sys.stdout", new_callable=StringIO):
            from query_normalizer.cli import cli

            cli()
    finally:
        sys.argv = original_argv
