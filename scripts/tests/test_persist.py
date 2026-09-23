#!/usr/bin/env python3
"""Tests for scripts/persist-save and scripts/persist-restore-once.

These two scripts replace tmux-continuum, whose save and restore were both
gated behind a `ps`-based "is another tmux server running" heuristic that this
machine trips permanently (a tmux inside the rms container, plus one process
per WezTerm client). The whole value of the replacement is in its guards, so
the guards are what these tests pin down.

Everything runs against a stub tmux and stub resurrect scripts, under a
throwaway HOME — the real server and the real snapshots are never touched.

Run: python3 -m unittest discover -s scripts/tests
"""

import os
import pathlib
import subprocess
import tempfile
import time
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parents[1]
STUB_TMUX = pathlib.Path(__file__).resolve().parent / "stub_tmux.py"

# Records the arguments AND $TMUX, because restore.sh derives the socket from it.
RECORDER = """#!/bin/sh
printf 'TMUX=%s %s\\n' "$TMUX" "$*" >> "$STUB_DIR/{name}"
exit {rc}
"""


class PersistTestCase(unittest.TestCase):
    """A throwaway HOME with stubbed tmux and stubbed resurrect scripts."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)

        self.home = self.root / "home"
        self.stub = self.root / "stub"
        self.bin = self.root / "bin"
        for path in (self.home, self.stub, self.bin):
            path.mkdir(parents=True)

        # tmux on PATH -> the stub
        tmux = self.bin / "tmux"
        tmux.write_text(f'#!/bin/sh\nexec {STUB_TMUX} "$@"\n')
        tmux.chmod(0o755)

        # the resurrect plugin the scripts call into
        self.plugin = self.home / ".config/tmux/plugins/tmux-resurrect/scripts"
        self.plugin.mkdir(parents=True)
        self.write_recorder(self.plugin / "save.sh", "save_called")
        self.write_recorder(self.plugin / "restore.sh", "restore_called")

        self.resurrect = self.home / ".local/share/tmux/resurrect"
        self.resurrect.mkdir(parents=True)

        self.socket_dir = self.root / "sockets" / f"tmux-{os.getuid()}"
        self.socket_dir.mkdir(parents=True)
        self.set("socket_path", str(self.socket_dir / "default"))
        # A server that has just come up: the restore is only meant to fire
        # into one of those, so this is the default for these tests.
        self.set("start_time", str(int(time.time())))
        self.set("clients", "1")

    # --- helpers ---------------------------------------------------------

    def write_recorder(self, path, name, rc=0):
        path.write_text(RECORDER.format(name=name, rc=rc))
        path.chmod(0o755)

    def set(self, name, value):
        (self.stub / name).write_text(str(value))

    def get(self, name, default=""):
        path = self.stub / name
        return path.read_text().strip() if path.exists() else default

    def called(self, name):
        return (self.stub / name).exists()

    def log(self):
        path = self.home / ".local/state/anticrab-tmux/persist.log"
        return path.read_text() if path.exists() else ""

    def run_script(self, name, **env_extra):
        env = dict(
            os.environ,
            HOME=str(self.home),
            PATH=f"{self.bin}:{os.environ['PATH']}",
            STUB_DIR=str(self.stub),
            TMUX_TMPDIR=str(self.root / "sockets"),
            **env_extra,
        )
        env.pop("TMUX", None)
        env.pop("XDG_STATE_HOME", None)
        return subprocess.run([str(SCRIPTS / name)], capture_output=True,
                              text=True, env=env, timeout=60)


class PersistSave(PersistTestCase):
    def test_saves_when_the_server_is_ready(self):
        self.set("latch", "ready")
        self.run_script("persist-save")
        self.assertTrue(self.called("save_called"), self.log())

    def test_passes_quiet_so_the_save_does_not_touch_the_display(self):
        self.set("latch", "ready")
        self.run_script("persist-save")
        self.assertIn("quiet", (self.stub / "save_called").read_text())

    def test_does_not_save_when_no_server_is_running(self):
        self.set("latch", "ready")
        self.set("has_session", "0")
        self.run_script("persist-save")
        self.assertFalse(self.called("save_called"))

    def test_does_not_save_before_the_restore_has_finished(self):
        self.set("latch", "restoring")
        self.run_script("persist-save")
        self.assertFalse(self.called("save_called"))

    def test_does_not_save_from_a_scratch_server(self):
        self.set("latch", "scratch")
        self.run_script("persist-save")
        self.assertFalse(self.called("save_called"))

    def test_does_not_save_when_the_latch_was_never_set(self):
        self.set("latch", "")
        self.run_script("persist-save")
        self.assertFalse(self.called("save_called"))

    def test_records_every_outcome_in_the_log(self):
        self.set("latch", "restoring")
        self.run_script("persist-save")
        self.assertIn("restoring", self.log())

    def test_a_missing_server_is_not_an_error(self):
        self.set("latch", "ready")
        self.set("has_session", "0")
        self.assertEqual(self.run_script("persist-save").returncode, 0)

    def test_reports_a_failing_save(self):
        self.set("latch", "ready")
        self.write_recorder(self.plugin / "save.sh", "save_called", rc=1)
        self.run_script("persist-save")
        self.assertIn("FAILED", self.log())


class PersistRestoreOnce(PersistTestCase):
    def test_restores_into_a_freshly_started_server(self):
        (self.resurrect / "last").write_text("snapshot")
        self.run_script("persist-restore-once")
        self.assertTrue(self.called("restore_called"), self.log())

    def test_arms_saving_once_the_restore_is_done(self):
        (self.resurrect / "last").write_text("snapshot")
        self.run_script("persist-restore-once")
        self.assertEqual(self.get("latch"), "ready")

    def test_does_nothing_the_second_time_it_runs(self):
        (self.resurrect / "last").write_text("snapshot")
        self.set("latch", "ready")
        self.run_script("persist-restore-once")
        self.assertFalse(self.called("restore_called"))

    def test_does_not_restore_over_a_server_that_was_already_running(self):
        (self.resurrect / "last").write_text("snapshot")
        self.set("start_time", "1")  # epoch 1 — far older than 15s
        self.run_script("persist-restore-once")
        self.assertFalse(self.called("restore_called"))

    def test_an_already_running_server_still_gets_saving_armed(self):
        (self.resurrect / "last").write_text("snapshot")
        self.set("start_time", "1")
        self.run_script("persist-restore-once")
        self.assertEqual(self.get("latch"), "ready")

    def test_a_scratch_server_neither_restores_nor_saves(self):
        (self.resurrect / "last").write_text("snapshot")
        self.set("socket_path", str(self.socket_dir / "check"))
        self.run_script("persist-restore-once")
        self.assertFalse(self.called("restore_called"))
        self.assertEqual(self.get("latch"), "scratch")

    def test_nothing_to_restore_is_not_an_error(self):
        result = self.run_script("persist-restore-once")
        self.assertEqual(result.returncode, 0)
        self.assertFalse(self.called("restore_called"))
        self.assertEqual(self.get("latch"), "ready")

    def test_says_in_the_log_that_there_was_nothing_to_restore(self):
        self.run_script("persist-restore-once")
        self.assertIn("nothing to restore", self.log())

    def test_waits_for_a_client_before_restoring(self):
        # restore.sh switch-clients onto the saved session; with no client
        # attached those steps are silently dropped.
        (self.resurrect / "last").write_text("snapshot")
        self.set("clients", "0")
        self.run_script("persist-restore-once", ANTICRAB_TMUX_CLIENT_WAIT="2")
        self.assertIn("no client attached", self.log())

    def test_hands_restore_a_usable_TMUX_value(self):
        # restore.sh derives the socket from $TMUX; empty means `tmux -S ""`.
        (self.resurrect / "last").write_text("snapshot")
        self.run_script("persist-restore-once")
        self.assertRegex((self.stub / "restore_called").read_text(), r"TMUX=\S+,\d+,\d+")


class PersistStatus(PersistTestCase):
    """The detector. Everything above can stall silently; this is what says so."""

    def setUp(self):
        super().setUp()
        systemctl = self.bin / "systemctl"
        systemctl.write_text(
            '#!/bin/sh\n'
            'case "$*" in\n'
            '  *is-active*)  cat "$STUB_DIR/timer_active"  2>/dev/null || echo active ;;\n'
            '  *is-enabled*) cat "$STUB_DIR/timer_enabled" 2>/dev/null || echo enabled ;;\n'
            '  *) : ;;\n'
            'esac\n'
        )
        systemctl.chmod(0o755)
        self.set("latch", "ready")

    def snapshot(self, panes=3, age_minutes=0):
        name = "tmux_resurrect_20260923T000000.txt"
        path = self.resurrect / name
        path.write_text("".join(f"pane\tmain\t{i}\n" for i in range(panes)))
        stamp = int(time.time()) - age_minutes * 60
        os.utime(path, (stamp, stamp))
        link = self.resurrect / "last"
        if link.exists() or link.is_symlink():
            link.unlink()
        link.symlink_to(name)
        return path

    def test_is_happy_when_everything_works(self):
        self.snapshot()
        result = self.run_script("persist-status")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_reports_how_many_panes_are_in_the_snapshot(self):
        self.snapshot(panes=7)
        self.assertIn("7", self.run_script("persist-status").stdout)

    def test_complains_when_saving_is_not_armed(self):
        self.snapshot()
        self.set("latch", "restoring")
        result = self.run_script("persist-status")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("restoring", result.stdout)

    def test_complains_when_the_latch_was_never_set(self):
        self.snapshot()
        self.set("latch", "")
        self.assertNotEqual(self.run_script("persist-status").returncode, 0)

    def test_complains_when_the_snapshot_has_gone_stale(self):
        self.snapshot(age_minutes=40)
        result = self.run_script("persist-status")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("saving has stopped", result.stdout)

    def test_complains_when_the_timer_is_not_running(self):
        self.snapshot()
        self.set("timer_active", "inactive")
        result = self.run_script("persist-status")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("inactive", result.stdout)

    def test_complains_when_there_is_no_snapshot_at_all(self):
        result = self.run_script("persist-status")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no snapshot", result.stdout)

    def test_a_stopped_server_is_reported_but_is_not_a_failure(self):
        self.snapshot()
        self.set("has_session", "0")
        result = self.run_script("persist-status")
        self.assertIn("not running", result.stdout)
        self.assertEqual(result.returncode, 0)


class RestoreList(unittest.TestCase):
    """What tmux.conf's @resurrect-processes actually does, run through the real plugin.

    The point of the option is that nvim comes back and nothing else does.
    Both halves are easy to break by editing one string, and neither shows up
    until the next reboot — hence this, which feeds the value straight out of
    tmux.conf to resurrect's own matcher.
    """

    PLUGIN = pathlib.Path.home() / ".config/tmux/plugins/tmux-resurrect/scripts"
    SNAP_NVIM = "/snap/nvim/4860/usr/bin/nvim"

    @classmethod
    def setUpClass(cls):
        if not (cls.PLUGIN / "process_restore_helpers.sh").exists():
            raise unittest.SkipTest("tmux-resurrect is not installed")
        conf = (SCRIPTS.parent / "tmux.conf").read_text()
        cls.processes = None
        for line in conf.splitlines():
            line = line.strip()
            if line.startswith("set -g @resurrect-processes"):
                cls.processes = line.split("@resurrect-processes", 1)[1].strip().strip("'")
        if cls.processes is None:
            raise AssertionError("tmux.conf no longer sets @resurrect-processes")

    def strategy_for(self, command):
        """resurrect's own answer to 'what would you run for this pane?'"""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        binary = pathlib.Path(tmp.name) / "tmux"
        binary.write_text(
            '#!/bin/sh\n'
            'case "$*" in\n'
            f'  *@resurrect-processes*) printf %s \'{self.processes}\' ;;\n'
            '  *) : ;;\n'
            'esac\n'
        )
        binary.chmod(0o755)
        script = (
            f'cd {self.PLUGIN.parent} && . scripts/variables.sh && . scripts/helpers.sh '
            f'&& . scripts/process_restore_helpers.sh && _get_inline_strategy "{command}"'
        )
        env = dict(os.environ, PATH=f"{tmp.name}:{os.environ['PATH']}")
        done = subprocess.run(["bash", "-c", script], capture_output=True, text=True, env=env)
        return done.stdout.strip()

    def test_a_snap_nvim_is_restored_as_a_bare_nvim(self):
        # The saved command is the snap's revision-pinned absolute path; the
        # revision is gone from disk after the next snap refresh, so the
        # rewrite is what makes the restore survive an update at all.
        self.assertEqual(self.strategy_for(self.SNAP_NVIM), "nvim")

    def test_claude_is_not_restored(self):
        # Relaunching several Claude Code TUIs at login, none of which could
        # resume the right conversation anyway.
        self.assertEqual(self.strategy_for("claude -c"), "")

    def test_make_is_not_restored(self):
        # `make up` runs an unattended docker compose build and arms a teardown.
        self.assertEqual(self.strategy_for("make up"), "")
        self.assertEqual(self.strategy_for("make exec"), "")

    def test_a_plain_shell_is_not_restored(self):
        self.assertEqual(self.strategy_for("bash"), "")


if __name__ == "__main__":
    unittest.main()
