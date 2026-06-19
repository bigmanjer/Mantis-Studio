# -*- coding: utf-8 -*-

import argparse
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=10)
    parser.add_argument("--delay", type=int, default=80, help="Milliseconds between ticks.")
    args = parser.parse_args()

    steps = max(1, args.steps)
    delay = max(0, args.delay) / 1000

    for index in range(1, steps + 1):
        bar = "\u2588" * index + "\u2591" * (steps - index)
        sys.stdout.write(f"\r   [{bar}]")
        sys.stdout.flush()
        time.sleep(delay)

    sys.stdout.write("\n\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
