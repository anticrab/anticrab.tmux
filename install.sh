#!/usr/bin/env bash
# Bootstrap: symlink tmux.conf into XDG config dir and clone TPM.
# Idempotent — safe to run repeatedly.

set -euo pipefail

REPO_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TARGET_DIR="$HOME/.config/tmux"
TARGET_CONF="$TARGET_DIR/tmux.conf"
TPM_DIR="$TARGET_DIR/plugins/tpm"

mkdir -p "$TARGET_DIR"

if [[ -e "$TARGET_CONF" && ! -L "$TARGET_CONF" ]]; then
    backup="$TARGET_CONF.bak.$(date +%Y%m%d-%H%M%S)"
    echo "Existing $TARGET_CONF is not a symlink — moving to $backup"
    mv "$TARGET_CONF" "$backup"
fi
ln -sfn "$REPO_DIR/tmux.conf" "$TARGET_CONF"
echo "Linked: $TARGET_CONF -> $REPO_DIR/tmux.conf"

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
