#!/usr/bin/env python3
"""A stand-in for the tmux binary, for the persist-* tests.

Answers only the queries the persist scripts make, from files in $STUB_DIR, and
appends every invocation to $STUB_DIR/calls so a test can assert on what was
asked. Keeps the real tmux server on this machine completely out of the tests.
"""

import os
import pathlib
import sys

STUB = pathlib.Path(os.environ["STUB_DIR"])


def read(name, default=""):
    path = STUB / name
    return path.read_text().strip() if path.exists() else default


def main():
    args = sys.argv[1:]
    with (STUB / "calls").open("a") as handle:
        handle.write(" ".join(args) + "\n")

    # Drop the flags that only pick a server; the stub has just one.
    positional = []
    index = 0
    while index < len(args):
        if args[index] == "-N":
            index += 1
        elif args[index] in ("-S", "-L", "-f"):
            index += 2
        else:
            positional.append(args[index])
            index += 1

    if not positional:
        return 0
    command, rest = positional[0], positional[1:]

    if command == "has-session":
        return 0 if read("has_session", "1") == "1" else 1

    if command == "show-option":
        return print_option(rest)

    if command == "set-option":
        # set-option -gq @anticrab-persist <value>
        if len(rest) >= 2:
            (STUB / "latch").write_text(rest[-1])
        return 0

    if command == "display-message":
        fmt = rest[-1] if rest else ""
        fmt = fmt.replace("#{socket_path}", read("socket_path"))
        fmt = fmt.replace("#{start_time}", read("start_time", "0"))
        fmt = fmt.replace("#{pid}", read("pid", "4242"))
        print(fmt)
        return 0

    if command == "list-clients":
        for name in range(int(read("clients", "1"))):
            print(f"/dev/pts/{name}")
        return 0

    if command == "list-sessions":
        print(read("sessions", "main"))
        return 0

    return 0


def print_option(rest):
    if "@anticrab-persist" in rest:
        print(read("latch"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
