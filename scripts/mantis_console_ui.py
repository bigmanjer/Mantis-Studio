"""Console rendering helpers for the MANTIS launcher chat."""

from __future__ import annotations

import os
import sys
import textwrap
import time


class ConsoleUI:
    FRAME_WIDTH = 68

    def __init__(self) -> None:
        self.use_color = self.enable_ansi_color()
        self.use_native_color = (not self.use_color) and self.supports_native_color()
        self.use_unicode = False

    def prompt(self) -> str:
        if not self.use_color:
            self.set_native_color("blue")
            return "  YOU > "
        return "\033[94m  YOU \033[96m>\033[0m "

    def reset_color(self) -> None:
        if self.use_color:
            print("\033[0m", end="")
        elif self.use_native_color:
            self.set_native_color("soft")

    def print_banner(self) -> None:
        if self.use_unicode:
            lines = self.unicode_banner()
        else:
            lines = self.ascii_banner()
        for line in lines:
            print(self.color(line, "green"))

    @staticmethod
    def unicode_banner() -> list[str]:
        return [
            "╔" + "═" * 63 + "╗",
            "║" + " " * 63 + "║",
            "║       ███╗   ███╗ █████╗ ███╗   ██╗████████╗██╗███████╗       ║",
            "║       ████╗ ████║██╔══██╗████╗  ██║╚══██╔══╝██║██╔════╝       ║",
            "║       ██ ████ ██║███████║██ ██╗ ██║   ██║   ██║██║            ║",
            "║       ██╔████╔██║███████║██╔╗██ ██║   ██║   ██║███████╗       ║",
            "║       ██║╚██╔╝██║██╔══██║██║╚██╗██║   ██║   ██║╚════██║       ║",
            "║       ██║ ╚═╝ ██║██║  ██║██║ ╚████║   ██║   ██║     ██║       ║",
            "║       ██║     ██║██║  ██║██║  ████║   ██║   ██║███████║       ║",
            "║       ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚══════╝       ║",
            "║         Modular AI Narrative Text Intelligence System         ║",
            "╚" + "═" * 63 + "╝",
        ]

    @staticmethod
    def ascii_banner() -> list[str]:
        return [
            "  +------------------------------------------------------------------+",
            "  |                                                                  |",
            "  |      ##     ##    ###    ##    ## ######## ####  ######          |",
            "  |      ###   ###   ## ##   ###   ##    ##     ##  ##    ##         |",
            "  |      #### ####  ##   ##  ####  ##    ##     ##  ##               |",
            "  |      ## ### ## ######### ## ## ##    ##     ##   ######          |",
            "  |      ##     ## ##     ## ##  ####    ##     ##        ##         |",
            "  |      ##     ## ##     ## ##   ###    ##     ##  ##    ##         |",
            "  |      ##     ## ##     ## ##    ##    ##    ####  ######          |",
            "  |                                                                  |",
            "  |         Modular AI Narrative Text Intelligence System            |",
            "  |             LOCAL INTELLIGENCE CONSOLE // MANTIS STUDIO          |",
            "  |                                                                  |",
            "  +------------------------------------------------------------------+",
        ]

    def print_status_line(self, label: str, value: str) -> None:
        label_text = f"{label.upper():<8}"
        print(f"  {self.color('[' + label_text + ']', 'green')} {self.color(value, 'soft')}")

    def print_panel(self, title: str, rows: list[tuple[str, str]]) -> None:
        width = self.FRAME_WIDTH
        print(self.color("  +" + "=" * (width - 2) + "+", "green"))
        print(self.color("  |", "green") + self.color(f" {title:<{width - 4}}", "cyan") + self.color("|", "green"))
        print(self.color("  |" + "-" * (width - 2) + "|", "green"))
        for label, value in rows:
            value_width = width - 15
            wrapped = textwrap.wrap(value, width=value_width) or [""]
            for idx, chunk in enumerate(wrapped):
                row_label = label if idx == 0 else ""
                text = f" {row_label:<10} {chunk}"
                print(self.color("  |", "green") + f"{text:<{width - 2}}" + self.color("|", "green"))
        print(self.color("  +" + "=" * (width - 2) + "+", "green"))

    def print_handoff_row(self, label: str, value: str) -> None:
        label_text = f"  {label:<8} "
        value_text = f"{value:<50}"[:50]
        print(
            self.color("  |", "green")
            + self.color(label_text, "cyan")
            + self.color(value_text, "soft")
            + self.color("|", "green")
        )

    def thinking_pulse(self, label: str) -> None:
        if not sys.stdin.isatty():
            return
        for filled in (3, 7, 10):
            if self.use_native_color and not self.use_color:
                print("\r  ", end="")
                self.set_native_color("green")
                print("MANTIS >", end="")
                self.set_native_color("soft")
                print(f" {label} ", end="")
                self.set_native_color("green")
                print(self.plain_bar(filled, 10), end="", flush=True)
            else:
                status = self.color("MANTIS >", "green")
                print(f"\r  {status} {self.color(label, 'soft')} {self.bar(filled, 10)}", end="", flush=True)
            self.sleep(0.06)
        self.reset_color()
        print("\n")

    def bar(self, filled: int, total: int) -> str:
        return self.color(self.plain_bar(filled, total), "green")

    @staticmethod
    def plain_bar(filled: int, total: int) -> str:
        filled = max(0, min(filled, total))
        full, empty = "\u2588", "\u2591"
        encoding = sys.stdout.encoding or ""
        try:
            (full + empty).encode(encoding or "utf-8")
        except (LookupError, UnicodeEncodeError):
            full, empty = "#", "-"
        bar = full * filled + empty * (total - filled)
        return f"[{bar}]"

    def color(self, text: str, color: str) -> str:
        if not self.use_color:
            return text
        colors = {
            "blue": "\033[94m",
            "cyan": "\033[96m",
            "green": "\033[92m",
            "yellow": "\033[93m",
            "soft": "\033[97m",
            "dim": "\033[90m",
            "reset": "\033[0m",
        }
        return f"{colors.get(color, '')}{text}{colors['reset']}"

    @staticmethod
    def sleep(seconds: float) -> None:
        try:
            time.sleep(seconds)
        except Exception:
            pass
    @staticmethod
    def supports_unicode() -> bool:
        encoding = (sys.stdout.encoding or "").lower()
        return "utf" in encoding or "65001" in encoding

    @staticmethod
    def enable_ansi_color() -> bool:
        if not sys.stdout.isatty():
            return False
        if os.name != "nt":
            return True
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)
            mode = ctypes.c_uint32()
            if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                return False
            enable_virtual_terminal = 0x0004
            if kernel32.SetConsoleMode(handle, mode.value | enable_virtual_terminal):
                return True
        except Exception:
            return False
        return False

    @staticmethod
    def supports_native_color() -> bool:
        return os.name == "nt" and sys.stdout.isatty()

    def set_native_color(self, color: str) -> None:
        if not self.use_native_color:
            return
        attrs = {
            "blue": 0x09,
            "green": 0x0A,
            "yellow": 0x0E,
            "cyan": 0x0B,
            "soft": 0x0F,
            "dim": 0x08,
        }
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)
            kernel32.SetConsoleTextAttribute(handle, attrs.get(color, 0x0F))
        except Exception:
            pass
