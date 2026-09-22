#!/usr/bin/env python3
"""Tests for scripts/clean-copy — the copy-mode selection cleaner.

Run: python3 -m unittest discover -s scripts/tests
The script is exercised as a subprocess, the same way tmux runs it.
"""

import pathlib
import subprocess
import unittest

CLEAN_COPY = pathlib.Path(__file__).resolve().parents[1] / "clean-copy"


def clean(text, start_col=None):
    cmd = [str(CLEAN_COPY)]
    if start_col is not None:
        cmd += ["--start-col", str(start_col)]
    done = subprocess.run(cmd, input=text, capture_output=True, text=True, check=True)
    assert done.stderr == "", f"unexpected stderr: {done.stderr!r}"
    return done.stdout


class TrailingWhitespace(unittest.TestCase):
    def test_strips_trailing_spaces_from_every_line(self):
        self.assertEqual(clean("alpha   \nbeta\t\n"), "alpha\nbeta")

    def test_turns_whitespace_only_lines_into_empty_lines(self):
        self.assertEqual(clean("alpha\n    \nbeta\n"), "alpha\n\nbeta")


class Dedent(unittest.TestCase):
    def test_removes_the_indent_shared_by_all_lines(self):
        self.assertEqual(clean("  alpha\n  beta\n"), "alpha\nbeta")

    def test_keeps_relative_indentation(self):
        self.assertEqual(clean("  alpha\n      beta\n"), "alpha\n    beta")

    def test_does_not_dedent_a_block_whose_first_line_is_flush_left(self):
        self.assertEqual(
            clean("def f():\n    return 1\n"),
            "def f():\n    return 1",
        )

    def test_ignores_blank_lines_when_measuring_the_indent(self):
        self.assertEqual(clean("  alpha\n\n  beta\n"), "alpha\n\nbeta")


class SelectionStartedMidLine(unittest.TestCase):
    def test_dedents_the_remaining_lines_by_their_own_indent(self):
        # Drag started at column 2 of "  alpha", so the first line arrives
        # without its indent while the rest keep theirs.
        self.assertEqual(clean("alpha\n  beta\n", start_col=2), "alpha\nbeta")

    def test_keeps_relative_indentation_of_a_block_selected_from_its_text(self):
        # The rows were "    def f():" / "        return 1" and the drag began
        # at column 4, on the first character. The first line therefore arrives
        # flush left while the body still carries all eight of its spaces — the
        # body must stay indented relative to `def`.
        self.assertEqual(
            clean("def f():\n        return 1\n", start_col=4),
            "def f():\n    return 1",
        )

    def test_strips_leading_whitespace_of_the_partial_first_line(self):
        self.assertEqual(clean("  alpha\n      beta\n", start_col=4), "alpha\nbeta")

    def test_start_col_zero_measures_the_first_line_too(self):
        self.assertEqual(
            clean("def f():\n    return 1\n", start_col=0),
            "def f():\n    return 1",
        )


class Edges(unittest.TestCase):
    def test_drops_blank_lines_at_both_ends(self):
        self.assertEqual(clean("\n\nalpha\n\n\n"), "alpha")

    def test_drops_the_final_newline_so_a_pasted_command_is_not_run(self):
        self.assertEqual(clean("git status\n"), "git status")

    def test_keeps_a_single_line_as_is(self):
        self.assertEqual(clean("git status"), "git status")

    def test_empty_input_gives_empty_output(self):
        self.assertEqual(clean(""), "")

    def test_whitespace_only_input_gives_empty_output(self):
        self.assertEqual(clean("   \n  \n"), "")


if __name__ == "__main__":
    unittest.main()
