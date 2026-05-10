# anticrab.tmux

Personal tmux config. Companion to [anticrab.nvim](https://github.com/anticrab/anticrab.nvim) — `vim-tmux-navigator` lets `Ctrl-h/j/k/l` move seamlessly between nvim splits and tmux panes.

Tested on Ubuntu 24.04 + tmux 3.4 + GNOME Wayland.

## Install

```bash
git clone https://github.com/<you>/anticrab.tmux ~/projects/anticrab.tmux
cd ~/projects/anticrab.tmux
./install.sh
```

The script:
- symlinks `tmux.conf` to `~/.config/tmux/tmux.conf` (backs up an existing non-symlink),
- clones [TPM](https://github.com/tmux-plugins/tpm) to `~/.config/tmux/plugins/tpm`.

After it finishes, start tmux and press **`Ctrl-a` then `I`** (capital `I`) to install plugins.

> If a tmux server is already running, kill it first: `tmux kill-server`. Otherwise it keeps the old config in memory.

### Optional system packages

| Package | Why |
|---|---|
| `wl-clipboard` | Yank to system clipboard on Wayland (`sudo apt install wl-clipboard`) |
| `xclip` | Same, for X11 sessions (`sudo apt install xclip`) |
| A Nerd Font | catppuccin status bar uses ligature glyphs |

The config auto-detects Wayland vs. X11 and uses whichever clipboard tool is on `PATH`.

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
