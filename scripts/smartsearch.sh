#!/usr/bin/env bash
# Smart-case search for tmux copy-mode.
#
# Invoked by the `/` and `?` bindings in tmux.conf:
#   1. The binding enters copy-mode and opens command-prompt.
#   2. The user types a pattern, which tmux puts into env var
#      _TMUX_SEARCH_PATTERN via `set-environment -g`.
#   3. This script reads it, decides smart-case, and dispatches
#      `send-keys -X search-<direction> -r ...` back into copy-mode.
#
# Smart-case rule (same as vim's 'smartcase'):
#   - Pattern has any uppercase letter → case-sensitive (passed verbatim).
#   - All lowercase → case-insensitive (each letter wrapped in [aA] form).
#
# POSIX ERE (which tmux uses via regcomp) has no `(?i)` inline flag, so the
# char-class wrap is the only portable way.

set -euo pipefail

direction="${1:?usage: smartsearch.sh <backward|forward>}"

pattern=$(tmux show-environment -g _TMUX_SEARCH_PATTERN 2>/dev/null \
              | sed 's/^_TMUX_SEARCH_PATTERN=//')
tmux set-environment -gu _TMUX_SEARCH_PATTERN  # one-shot, clear after use

[ -z "$pattern" ] && exit 0

if printf '%s' "$pattern" | LC_ALL=C grep -q '[[:upper:]]'; then
    final="$pattern"
else
    final=$(printf '%s' "$pattern" | sed 's/\([a-zA-Z]\)/[\L\1\U\1]/g')
fi

tmux send-keys -X "search-$direction" "$final"
