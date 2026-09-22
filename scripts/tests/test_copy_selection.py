#!/usr/bin/env python3
"""Tests for scripts/copy-selection — the clipboard side of copy mode.

The clipboard tools (wl-copy, xclip) and tmux itself are replaced by stub
executables on PATH that record what they were handed, so the test checks the
real script end to end without touching the session's clipboard.

Run: python3 -m unittest discover -s scripts/tests
"""

import os
import pathlib
import subprocess
import tempfile
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parents[1]
COPY_SELECTION = SCRIPTS / "copy-selection"

STUB = """#!/bin/sh
printf '%s' "$*" > "$RECORD_DIR/{name}.args"
cat > "$RECORD_DIR/{name}.stdin"
"""


class CopySelection(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.record = pathlib.Path(self.tmp.name) / "record"
        self.bin = pathlib.Path(self.tmp.name) / "bin"
        self.record.mkdir()
        self.bin.mkdir()
        self.addCleanup(self.tmp.cleanup)

    def stub(self, name):
        path = self.bin / name
        path.write_text(STUB.format(name=name))
        path.chmod(0o755)

    def run_script(self, text, *args, wayland="wayland-0"):
        env = dict(
            os.environ,
            PATH=f"{self.bin}:{os.environ['PATH']}",
            RECORD_DIR=str(self.record),
            WAYLAND_DISPLAY=wayland,
        )
        return subprocess.run(
            [str(COPY_SELECTION), *args],
            input=text,
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )

    def recorded(self, name, suffix="stdin"):
        path = self.record / f"{name}.{suffix}"
        return path.read_text() if path.exists() else None

    def recorded_args(self, name):
        args = self.recorded(name, "args")
        self.assertIsNotNone(args, f"{name} was never called")
        return args or ""

    def test_sends_the_cleaned_selection_to_the_wayland_clipboard(self):
        self.stub("wl-copy")
        self.stub("tmux")
        self.run_script("  alpha   \n  beta\n")
        self.assertEqual(self.recorded("wl-copy"), "alpha\nbeta")

    def test_also_loads_the_cleaned_text_into_a_tmux_buffer(self):
        self.stub("wl-copy")
        self.stub("tmux")
        self.run_script("  alpha\n  beta\n")
        self.assertEqual(self.recorded("tmux"), "alpha\nbeta")
        self.assertIn("load-buffer", self.recorded_args("tmux"))

    def test_passes_the_start_column_through_to_the_cleaner(self):
        self.stub("wl-copy")
        self.stub("tmux")
        # Drag started mid-line, so the first line keeps no indent of its own
        # and the rest are dedented by theirs.
        self.run_script("alpha\n    beta\n", "4")
        self.assertEqual(self.recorded("wl-copy"), "alpha\nbeta")

    def test_falls_back_to_xclip_without_wayland(self):
        self.stub("xclip")
        self.stub("tmux")
        self.run_script("alpha\n", wayland="")
        self.assertEqual(self.recorded("xclip"), "alpha")
        self.assertIn("clipboard", self.recorded_args("xclip"))

    def test_copies_nothing_when_the_selection_is_only_whitespace(self):
        self.stub("wl-copy")
        self.stub("tmux")
        self.run_script("   \n  \n")
        self.assertIsNone(self.recorded("wl-copy"))
        self.assertIsNone(self.recorded("tmux"))


if __name__ == "__main__":
    unittest.main()
