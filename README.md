# anticrab.tmux

Personal tmux config. Companion to [anticrab.nvim](https://github.com/anticrab/anticrab.nvim) — `vim-tmux-navigator` lets `Ctrl-h/j/k/l` move seamlessly between nvim splits and tmux panes.

Tested on Ubuntu 24.04 + tmux 3.4 + GNOME Wayland.

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
| `tmux` | The terminal multiplexer itself (≥ 3.0; tested on 3.4) |
| `git` | `install.sh` clones TPM; TPM clones every plugin |
| `wl-clipboard` *(Wayland)* / `xclip` *(X11)* | Yank to system clipboard from copy mode (`y` / mouse drag) |

The config auto-detects Wayland vs. X11 at load time and uses whichever clipboard tool is on `PATH`.

### Optional

- **A Nerd Font** in your terminal — the catppuccin status bar uses ligature glyphs. Pick one from <https://www.nerdfonts.com/font-downloads> (e.g. JetBrainsMono Nerd Font) and set it as your terminal font.

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
| `y` (in copy mode) | Yank to system clipboard, exit |
| Mouse drag | Yank to system clipboard, exit |
| `q` | Exit copy mode |

### Plugins (TPM)

| Keys | Action |
|---|---|
| `prefix I` | Install declared plugins |
| `prefix U` | Update plugins |
| `prefix Alt-u` | Uninstall plugins not in the conf |
| `prefix Ctrl-s` | Save session (tmux-resurrect) |
| `prefix Ctrl-r` | Restore session (tmux-resurrect) |

`tmux-continuum` saves the session every 15 min and restores it on `tmux` start, so manual save/restore is rarely needed.

## What's in here

- `tmux.conf` — the config (commented section by section)
- `install.sh` — symlink + TPM bootstrap
- `README.md` — this file

## Customization

Don't fork the repo just to tweak — drop a `~/.config/tmux/tmux.local.conf` and `source` it from `tmux.conf` if you want personal overrides without diverging from upstream. (Not done by default to keep the example minimal.)
