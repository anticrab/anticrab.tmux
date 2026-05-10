#!/usr/bin/env bash
# Bootstrap: place tmux.conf into XDG config dir and clone TPM.
# Idempotent — safe to run repeatedly.
#
# Modes (mutually exclusive):
#   (default)   If this repo is already at ~/.config/tmux, only TPM is cloned.
#               Otherwise, copy tmux.conf into ~/.config/tmux/tmux.conf.
#   --symlink   Symlink this repo's tmux.conf into ~/.config/tmux/tmux.conf
#               (useful if you keep the repo at ~/projects/anticrab.tmux and
#               want edits there to take effect immediately).
#
# In all modes, an existing non-symlink tmux.conf is moved to a timestamped
# backup before being replaced, so you never silently lose a hand-rolled config.

set -euo pipefail

REPO_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TARGET_DIR="$HOME/.config/tmux"
TARGET_CONF="$TARGET_DIR/tmux.conf"
TPM_DIR="$TARGET_DIR/plugins/tpm"

MODE="copy"
for arg in "$@"; do
    case "$arg" in
        --symlink) MODE="symlink" ;;
        --copy)    MODE="copy" ;;
        -h|--help)
            cat <<EOF
Usage: install.sh [--symlink]

Without flags: copy tmux.conf into ~/.config/tmux/ (or skip if the repo is
already there). With --symlink: symlink instead — useful for hacking on the
repo from ~/projects/anticrab.tmux.

In all modes TPM is cloned into ~/.config/tmux/plugins/tpm.
EOF
            exit 0 ;;
        *) echo "Unknown argument: $arg (try --help)" >&2; exit 1 ;;
    esac
done

mkdir -p "$TARGET_DIR"

backup_existing() {
    if [[ -e "$TARGET_CONF" || -L "$TARGET_CONF" ]]; then
        backup="$TARGET_CONF.bak.$(date +%Y%m%d-%H%M%S)"
        echo "Backing up existing $TARGET_CONF -> $backup"
        mv "$TARGET_CONF" "$backup"
    fi
}

if [[ "$REPO_DIR" == "$TARGET_DIR" ]]; then
    echo "Repo is already at $TARGET_DIR — config in place, nothing to do."
elif [[ "$MODE" == "symlink" ]]; then
    backup_existing
    ln -sfn "$REPO_DIR/tmux.conf" "$TARGET_CONF"
    echo "Linked: $TARGET_CONF -> $REPO_DIR/tmux.conf"
else
    backup_existing
    cp "$REPO_DIR/tmux.conf" "$TARGET_CONF"
    echo "Copied: $REPO_DIR/tmux.conf -> $TARGET_CONF"
fi

if [[ ! -d "$TPM_DIR" ]]; then
    echo "Cloning TPM..."
    git clone --depth 1 https://github.com/tmux-plugins/tpm "$TPM_DIR"
else
    echo "TPM already present at $TPM_DIR"
fi

# Clipboard helper hint (non-fatal).
if [[ -n "${WAYLAND_DISPLAY:-}" ]]; then
    if ! command -v wl-copy >/dev/null; then
        echo "Hint: 'sudo apt install wl-clipboard' enables yank-to-clipboard on Wayland."
    fi
else
    if ! command -v xclip >/dev/null; then
        echo "Hint: 'sudo apt install xclip' enables yank-to-clipboard on X11."
    fi
fi

cat <<'EOF'

Done. Next steps:
  1. Start tmux:                          tmux
  2. Inside tmux, install plugins:        Ctrl-a + I    (capital I)
  3. Reload config later with:            Ctrl-a + r

Restart any existing tmux server with `tmux kill-server` before reconnecting,
otherwise the old config keeps running.
EOF
