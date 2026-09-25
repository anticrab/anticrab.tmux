# anticrab.tmux

Personal tmux config. Companion to [anticrab.nvim](https://github.com/anticrab/anticrab.nvim) — `vim-tmux-navigator` lets `Ctrl-h/j/k/l` move seamlessly between nvim splits and tmux panes.

Tested on Ubuntu 24.04 + tmux 3.4 + GNOME Wayland.

Panes run zsh, configured by [anticrab.zsh](https://github.com/anticrab/anticrab.zsh) — `default-shell` and `default-command` name it explicitly, which is also what decides the shell of panes brought back by resurrect after a reboot.

## Install

### TL;DR — two commands

```bash
# 1. System dependencies (Wayland; for X11 swap wl-clipboard → xclip)
sudo apt update && sudo apt install -y tmux git wl-clipboard

# 2. Clone the config straight into ~/.config/tmux and bootstrap TPM
git clone https://github.com/anticrab/anticrab.tmux ~/.config/tmux \
    && ~/.config/tmux/install.sh
```

Then start tmux and install plugins:

```bash
tmux                    # start a session
# inside tmux:
#   Ctrl-a then I       (capital I) — install plugins via TPM
#   Ctrl-a then r       — reload config
```

> If a tmux server was already running, kill it first: `tmux kill-server`. Otherwise it keeps the old config in memory.
>
> If `~/.config/tmux/` already exists (e.g. from a previous setup), back it up first: `mv ~/.config/tmux ~/.config/tmux.bak.$(date +%s)`.

### What each package is for

| Package | Why it's needed |
|---|---|
| `tmux` | The terminal multiplexer itself (≥ 3.2 for the copy filter; tested on 3.4) |
| `git` | `install.sh` clones TPM; TPM clones every plugin |
| `wl-clipboard` *(Wayland)* / `xclip` *(X11)* | Copying from copy mode to the system clipboard |
| `python3` | `scripts/clean-copy`, the filter every copy goes through (preinstalled on Ubuntu) |

`scripts/copy-selection` picks the clipboard tool when you copy — `wl-copy` when a
Wayland display is set, `xclip` otherwise — and falls back to asking the outer
terminal for the clipboard over OSC 52 if neither is installed.

### Optional

- **A Nerd Font** in your terminal — for icons in the programs running inside (zvim's tabs and status line). Pick one from <https://www.nerdfonts.com/font-downloads> (e.g. JetBrainsMono Nerd Font) and set it as your terminal font.

### Alternative: symlink mode (for hacking on the config)

If you want to keep the repo somewhere else (e.g. `~/projects/anticrab.tmux`) and have edits there take effect immediately without copying, clone there and pass `--symlink`:

```bash
git clone https://github.com/anticrab/anticrab.tmux ~/projects/anticrab.tmux \
    && ~/projects/anticrab.tmux/install.sh --symlink
```

The script will symlink `~/projects/anticrab.tmux/tmux.conf` into `~/.config/tmux/tmux.conf`. From then on, every `git pull` (or local edit) is picked up by the next `Ctrl-a r` reload — no re-running `install.sh`.

### What `install.sh` does

- **Default (copy mode):** copies `tmux.conf` into `~/.config/tmux/tmux.conf`. If the repo is already at `~/.config/tmux/`, this step is a no-op (the file is already there).
- **`--symlink`:** symlinks the repo's `tmux.conf` into `~/.config/tmux/tmux.conf` instead.
- In both modes: backs up any existing `tmux.conf` to a timestamped `.bak.*` before replacing, and clones [TPM](https://github.com/tmux-plugins/tpm) into `~/.config/tmux/plugins/tpm` (skipped if already present).
- Idempotent — safe to re-run.

## Cheatsheet

Prefix is **`Ctrl-a`**. Press it twice (`Ctrl-a Ctrl-a`) to send a literal `Ctrl-a` to the foreground app.

### Sessions / windows

| Keys | Action |
|---|---|
| `prefix r` | Reload config |
| `prefix c` | New window in current dir |
| `prefix ,` | Rename window |
| `prefix Ctrl-p` / `prefix Ctrl-n` | Previous / next window (repeatable) |
| `prefix d` | Detach session |
| `prefix s` | Switch session |
| `prefix $` | Rename session |

### Panes

| Keys | Action |
|---|---|
| `prefix \|` | Vertical split (current dir) |
| `prefix -` | Horizontal split (current dir) |
| `prefix h/j/k/l` | Focus pane left/down/up/right |
| `Ctrl-h/j/k/l` | Same, **also crosses into nvim splits** (vim-tmux-navigator) |
| `prefix H/J/K/L` | Resize pane (repeatable while held) |
| `prefix z` | Zoom / unzoom current pane |
| `prefix x` | Kill pane |

### Copy mode

| Keys | Action |
|---|---|
| `prefix v` | Enter copy mode |
| `v` (in copy mode) | Begin selection |
| `Ctrl-v` (in copy mode) | Toggle rectangular selection |
| `y` / `Enter` (in copy mode) | Copy to the clipboard and leave copy mode |
| Mouse drag | Copy on release; the selection stays on screen |
| Double-click | Copy the word — a whole path, URL, `file.cpp:42` or `user@host` |
| Triple-click | Copy the line |
| Click | Clear the selection (and leave copy mode when scrolled to the bottom) |
| `Esc` / `q` | Leave copy mode |

Mouse copies deliberately keep the selection visible, so you can see what you
took. The flip side: the pane is still in copy mode afterwards, so click, `Esc`
or `q` before typing again — tmux has no "any key leaves copy mode".

**What lands on the clipboard is cleaned up first.** TUI programs paint a left
margin around their output, so a selection copied verbatim pastes with leading
spaces on every line. [`scripts/copy-selection`](scripts/copy-selection) drops
the trailing padding, the indent shared by every line, blank lines at the ends
and the final newline (so a pasted command doesn't run on its own). Relative
indentation survives — copy a function and its body stays indented under it.

That holds even when the drag began on the first character of an indented block,
because tmux hands the filter `#{selection_start_x}`: the columns before the drag
started belong to that line's indent.
[`scripts/clean-copy`](scripts/clean-copy) does the text work and has
[tests](scripts/tests):

```bash
python3 -m unittest discover -s scripts/tests
```

The selection reaches the script through `pipe-no-clear` rather than
`copy-pipe`, because copy-pipe would put the *unfiltered* text on the clipboard
itself before the filter ever ran. Exactly one write reaches the system
clipboard, so the GPaste history gets a single entry.

The gestures behave the same in the layers around tmux: WezTerm cleans its own
Shift+drag selections, zvim copies on mouse release, and Claude Code already
copies clean text.

### Plugins (TPM)

| Keys | Action |
|---|---|
| `prefix I` | Install declared plugins |
| `prefix U` | Update plugins |
| `prefix Alt-u` | Uninstall plugins not in the conf |
| `prefix Ctrl-s` | Save session (tmux-resurrect) |
| `prefix Ctrl-r` | Restore session (tmux-resurrect) |

Saving and restoring happen by themselves — see below. The manual keys are a
belt-and-braces option, not the mechanism.

## Sessions across a reboot

Sessions, window layouts, working directories and **each pane's scrollback** are
snapshotted every 5 minutes and the moment you close a WezTerm window, and
restored when the tmux server next starts.

```bash
~/.config/tmux/scripts/persist-status   # is my state actually being saved?
```

That one command is the point of the design, because the setup it replaced
failed silently for weeks. It reports the server, the save latch, the timer,
how old the newest snapshot is and how big the scrollback archive is, and exits
non-zero when any of it has stopped.

### Why not tmux-continuum

`tmux-continuum` is the obvious answer and it does not work here. Both of its
halves sit behind `another_tmux_server_running()`, which counts **every** uid
process whose argv starts with `tmux` — a tmux inside a Docker container, and
one process per WezTerm client, all count as rival servers
(`scripts/helpers.sh:25-49`). On this machine the check never passes, so it
installs neither its periodic save nor its boot restore, and TPM runs plugins
with output redirected to `/dev/null`, so nothing says so.

Its save is also structurally wrong for the case being solved: it works by
prepending `#(continuum_save.sh)` to `status-right`, and tmux only expands
`#()` while a client is drawing the status bar. A detached server — what the
machine has while it shuts down — is never saved.

So this repo owns both halves instead:

| Piece | What it does |
|---|---|
| [`scripts/persist-save`](scripts/persist-save) | Takes the snapshot. Refuses to run without a server, before the restore has finished, or from a scratch `tmux -L …` server — any of which would overwrite the good snapshot with a one-pane dump. |
| [`scripts/persist-restore-once`](scripts/persist-restore-once) | Restores, once per server. Latched on a global tmux option, so `prefix r` cannot re-restore; guarded on server age, so reloading the config on a live server arms saving and touches nothing. |
| [`scripts/persist-status`](scripts/persist-status) | Says whether the above is still working. |
| [`systemd/anticrab-tmux-save.timer`](systemd/) | Fires the save every 5 min, including while detached. Installed and enabled by `install.sh`. |
| `set-hook client-detached` / `session-closed` | Fires the save the instant a WezTerm window closes or a session is killed — the events that actually precede a reboot. |

Both scripts append to `~/.local/state/anticrab-tmux/persist.log`.

### What comes back, and what deliberately does not

**nvim** is restarted in its saved directory as a bare `nvim`, which hands
straight over to `auto-session` in
[anticrab.nvim](https://github.com/anticrab/anticrab.nvim) — it restores the
buffers, the config restores the editor. (The rewrite matters: `ps` records nvim
as `/snap/nvim/<rev>/usr/bin/nvim`, a path whose revision is gone after the next
snap refresh.) `less`, `man`, `top` and friends come back too, from resurrect's
own default list.

**`claude -c`, `make up`, `make exec` and plain shells do not.** `make up` would
start an unattended `docker compose up --build` at login and arm a teardown;
`claude -c` would relaunch several TUIs and still could not resume the right
conversation per pane. Those panes come back as shells in the right directory,
with their scrollback on screen.

> **Scrollback is stored in plaintext.** `@resurrect-capture-pane-contents` writes
> what was on each pane's screen — including anything a TUI was showing — to
> `~/.local/share/tmux/resurrect/pane_contents.tar.gz`, and snapshots are kept
> for 30 days. Roughly 320 KB compressed here. Turn it off with
> `set -g @resurrect-capture-pane-contents 'off'` if that trade isn't worth it.

## Look

JetBrains "Dark" — the CLion New UI scheme — set with plain tmux options (no
status-bar plugin). [anticrab.wezterm](https://github.com/anticrab/anticrab.wezterm)
and `jb.nvim` in [anticrab.nvim](https://github.com/anticrab/anticrab.nvim) carry
the same palette, so terminal, status bar and editor read as one program:

| Colour | Where |
|---|---|
| `#1e1f22` | editor / pane background (WezTerm paints it) |
| `#2b2d30` | status bar |
| `#43454a` | current window, messages |
| `#3574f0` | session name, active pane border |
| `#214283` | selection — also `Visual` in zvim and WezTerm's `selection_bg` |
| `#114957` | search matches in copy mode |

## What's in here

- `tmux.conf` — the config (commented section by section)
- `scripts/copy-selection` — clipboard side of copy mode (cleans, then copies)
- `scripts/clean-copy` — the text filter, with `scripts/tests`
- `scripts/smartsearch.sh` — smart-case search for copy mode (`prefix f` / `F`)
- `scripts/persist-save`, `scripts/persist-restore-once`, `scripts/persist-status` — session persistence, with `scripts/tests`
- `systemd/` — the user timer that drives the periodic snapshot
- `install.sh` — symlink + TPM bootstrap
- `README.md` — this file

## Customization

Don't fork the repo just to tweak — drop a `~/.config/tmux/tmux.local.conf` and `source` it from `tmux.conf` if you want personal overrides without diverging from upstream. (Not done by default to keep the example minimal.)
