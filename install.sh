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

# Backup an existing $1 unless it's already the symlink we'd create — that way
# re-running the script doesn't litter the dir with .bak files.
backup_unless_already_correct() {
    local path="$1" want_target="$2"
    if [[ -L "$path" ]]; then
        local cur_target
        cur_target="$(readlink "$path")"
        if [[ "$cur_target" == "$want_target" ]]; then
            return 1  # already correct — caller should skip the recreate
        fi
    fi
    if [[ -e "$path" || -L "$path" ]]; then
        local backup="$path.bak.$(date +%Y%m%d-%H%M%S)"
        echo "Backing up existing $path -> $backup"
        mv "$path" "$backup"
    fi
    return 0
}

if [[ "$REPO_DIR" == "$TARGET_DIR" ]]; then
    echo "Repo is already at $TARGET_DIR — config in place, nothing to do."
elif [[ "$MODE" == "symlink" ]]; then
    if backup_unless_already_correct "$TARGET_CONF" "$REPO_DIR/tmux.conf"; then
        ln -sfn "$REPO_DIR/tmux.conf" "$TARGET_CONF"
        echo "Linked: $TARGET_CONF -> $REPO_DIR/tmux.conf"
    else
        echo "Skipped: $TARGET_CONF already points to $REPO_DIR/tmux.conf"
    fi
    if backup_unless_already_correct "$TARGET_DIR/scripts" "$REPO_DIR/scripts"; then
        ln -sfn "$REPO_DIR/scripts" "$TARGET_DIR/scripts"
        echo "Linked: $TARGET_DIR/scripts -> $REPO_DIR/scripts"
    else
        echo "Skipped: $TARGET_DIR/scripts already points to $REPO_DIR/scripts"
    fi
else
    if backup_unless_already_correct "$TARGET_CONF" ""; then
        cp "$REPO_DIR/tmux.conf" "$TARGET_CONF"
        echo "Copied: $REPO_DIR/tmux.conf -> $TARGET_CONF"
    fi
    # Helper scripts referenced by tmux.conf (e.g. smartsearch.sh). Mirror
    # them into ~/.config/tmux/scripts/ so the paths in tmux.conf resolve.
    if [[ -d "$REPO_DIR/scripts" ]]; then
        mkdir -p "$TARGET_DIR/scripts"
        cp -p "$REPO_DIR/scripts/"* "$TARGET_DIR/scripts/"
        echo "Copied: $REPO_DIR/scripts/* -> $TARGET_DIR/scripts/"
    fi
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
