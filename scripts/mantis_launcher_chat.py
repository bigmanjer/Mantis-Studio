"""Conversational console assistant for the MANTIS Windows launcher.

This intentionally stays stdlib-only so the launcher can use it before the
full app dependency story is known.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import getpass
import json
import os
import re
import socket
import sys
import textwrap
import urllib.error
import urllib.request
import webbrowser
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    tomllib = None


@dataclass
class KeySource:
    label: str
    key: str


class LauncherChat:
    FRAME_WIDTH = 68

    def __init__(self, args: argparse.Namespace) -> None:
        self.url = args.url
        self.port = int(args.port)
        self.log_file = Path(args.log_file)
        self.chat_log_file = Path(args.chat_log_file)
        self.repo_root = Path(args.repo_root)
        self.history: list[tuple[str, str]] = []
        self.key_sources: list[KeySource] = []
        self.key_source_index = -1
        self.groq_key = ""
        self.groq_key_source = ""
        self.groq_base_url = "https://api.groq.com/openai/v1"
        self.groq_model = "llama3-8b-8192"
        self.use_color = sys.stdout.isatty()
        self.use_unicode = self._supports_unicode()
        self.memory_file = self.repo_root / "projects" / ".mantis_launcher_memory.json"
        self.memory = self._load_memory()
        self._load_groq_settings()

    def run(self) -> int:
        self._screen()
        self._log_event("system", f"chat started url={self.url} app_log={self.log_file}")
        self._boot_sequence()
        self._connect_groq()
        while True:
            try:
                user_text = input(self._prompt()).strip()
                self._reset_color()
            except (EOFError, KeyboardInterrupt):
                self._reset_color()
                self._log_event("system", "chat closed by eof/interrupt")
                print("\n  MANTIS > Closing launcher chat. The server may keep running.")
                return 0

            if not user_text:
                continue

            self._log_event("user", user_text)
            lowered = user_text.lower()
            if lowered in {"/exit", "/quit"}:
                self._log_event("system", "chat exited by user")
                print("  MANTIS > Standing down. MANTIS Studio can keep running in the background.")
                return 0

            self._thinking_pulse("MANTIS is thinking")
            answer = self.respond(user_text)
            self.history.append(("user", user_text))
            self.history.append(("mantis", answer))
            self._log_event("mantis", answer)
            print()
            print(self._wrap(answer))
            print()

    def respond(self, text: str) -> str:
        lowered = text.lower()

        if lowered.startswith("/"):
            return self.handle_command(lowered, text)
        if re.search(r"\bgsk_[A-Za-z0-9_-]{20,}\b", text):
            return "That looks like a secret key. I will not send it through chat. Use /save-key so I can store it safely."
        if self._user_is_claiming_creator_context(lowered):
            return (
                "Right. You are building MANTIS, not just using it. I should treat your feedback as product direction, "
                "not casual feature chatter. If you want me smarter, the real path is saved launcher memory, "
                "Knowledge Base retrieval, and measurable simulator/audit runs."
            )
        memory_note = self._extract_memory_request(text)
        if memory_note:
            return self.remember(memory_note)
        if self._asks_for_simulated_learning(lowered):
            return self.simulator_truth()
        if self._asks_about_connection(lowered):
            return (
                "I can become more capable, but I should stay coherent: part companion, part launcher operator, "
                "part writing partner. I do not need random web tricks to feel smart. I need better memory, "
                "better tone, and a few intentional tools that fit MANTIS."
            )
        if self._is_asking_about_groq_failure(lowered):
            return self.groq_fix_help()
        return self.ai_or_local(text, self.small_talk)

    def handle_command(self, lowered: str, original: str) -> str:
        command = lowered.strip()
        if command in {"/help", "/commands", "/?"}:
            return self.help_text()
        if command in {"/restart", "/relaunch", "/reload"}:
            return self.open_browser("I reopened the localhost window.")
        if command in {"/open", "/launch"}:
            return self.open_browser("I opened MANTIS Studio.")
        if command in {"/status", "/check", "/self-check", "/health"}:
            return self.self_check()
        if command in {"/logs", "/log"}:
            return self.summarize_logs()
        if command in {"/mantis", "/mantis-status", "/core", "/core-status", "/ai-status"}:
            return self.ai_status()
        if command == "/memory":
            return self.memory_summary()
        if command.startswith("/learn"):
            return self.remember(original.partition(" ")[2].strip())
        if command in {"/simulator", "/simulate", "/learning"}:
            return self.simulator_truth()
        if command in {"/save-key", "/save-mantis-key", "/key"}:
            return self.save_groq_key_interactive()
        if command in {"/clear", "/cls"}:
            self._screen()
            return "Fresh screen. Systems are still awake."
        if command in {"/exit", "/quit"}:
            return "Use exit or /exit at the prompt to close this chat."
        if re.search(r"\bgsk_[A-Za-z0-9_-]{20,}\b", original):
            return "That looks like a secret key. Use /save-key, then paste it into the hidden prompt."
        return "I do not know that slash command yet. Use /help to see what I can do."

    def ai_or_local(self, text: str, fallback) -> str:
        if self.groq_key:
            reply = self.ask_groq(text)
            if reply:
                return reply
            return fallback(text) + "\n\nMy higher reasoning layer did not answer cleanly, so I fell back to local mode."
        return fallback(text)

    def ask_groq(self, text: str) -> str | None:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are MANTIS, the conversational presence inside the MANTIS Studio "
                    "Windows launcher console. Your style should feel close to a warm coding partner: "
                    "curious, direct, playful when it fits, and genuinely present. "
                    "Do not sound like a generic chatbot, a help desk, or a status bot. "
                    "Do not say you are merely a local AI assistant. "
                    "Keep replies readable: short paragraphs, natural wording, and no dense walls of text. "
                    "Do not use markdown headings, code fences, fake loading bars, or fake progress percentages "
                    "unless the user explicitly asks for a written mockup. The launcher renders real status bars itself. "
                    "Do not claim you are working in the background, learning autonomously, checking files, "
                    "or providing automatic updates unless a real command/tool has been run. "
                    "Ask good follow-up questions when the user is exploring, but be decisive when they want action. "
                    "Launcher actions are slash commands like /help, /restart, /status, and /logs. "
                    "If the user casually mentions restarting or logs, discuss it conversationally unless "
                    "they use a slash command. If asked about current/live facts, be honest that you may not "
                    "have live lookup unless a specific tool is added. Help with writing, app operation, "
                    "troubleshooting, and normal conversation."
                ),
            },
            {
                "role": "system",
                "content": (
                    f"Runtime context: local URL {self.url}; port {self.port}; "
                    f"log file {self.log_file}; repo root {self.repo_root}."
                ),
            },
            {
                "role": "system",
                "content": (
                    "Persistent launcher memory currently saved for this user:\n"
                    f"{self._memory_prompt_context()}"
                ),
            },
        ]
        for speaker, content in self.history[-10:]:
            role = "assistant" if speaker == "mantis" else "user"
            messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": text})

        payload = {
            "model": self.groq_model,
            "messages": messages,
            "temperature": 0.72,
            "max_completion_tokens": 550,
        }
        data, error = self._post_groq(payload)
        if error:
            return error

        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError):
            return f"My upstream reasoning layer returned an unexpected response shape: {data!r}"

    def _post_groq(self, payload: dict[str, object]) -> tuple[dict[str, object], str | None]:
        last_error = ""
        tried_sources: list[str] = []

        while self.groq_key:
            tried_sources.append(self.groq_key_source)
            request = urllib.request.Request(
                f"{self.groq_base_url.rstrip('/')}/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {self.groq_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "MANTIS-Studio-Launcher/1.0",
                    "Accept": "application/json",
                },
                method="POST",
            )

            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    data = json.loads(response.read().decode("utf-8"))
                return data, None
            except urllib.error.HTTPError as exc:
                body = self._read_http_error(exc)
                last_error = self._groq_http_error_message(exc.code, body)
                if exc.code in {401, 403} and self._activate_next_key_source():
                    continue
                return {}, last_error
            except Exception as exc:  # pragma: no cover - depends on user network/key
                return {}, f"I reached for my higher reasoning layer, but the request failed: {exc}"

        if tried_sources:
            return {}, (
                "My higher reasoning layer rejected every saved access path I tried. "
                "Refresh the MANTIS intelligence key in AI Settings or use /save-key."
            )
        return {}, "My higher reasoning layer is not configured yet."

    def _activate_next_key_source(self) -> bool:
        next_index = self.key_source_index + 1
        if next_index >= len(self.key_sources):
            self.groq_key = ""
            self.groq_key_source = ""
            return False
        source = self.key_sources[next_index]
        self.key_source_index = next_index
        self.groq_key = source.key
        self.groq_key_source = source.label
        return True

    def _groq_http_error_message(self, status: int, body: str) -> str:
        details = self._extract_groq_error(body)
        if status in {401, 403}:
            if "1010" in body:
                return (
                    "The MANTIS intelligence gateway rejected this request with error code 1010. "
                    "That usually means the HTTP client looked incomplete or automated. "
                    "I have been updated to send a normal User-Agent header; restart the launcher chat "
                    "and try again. If it still happens, check VPN/proxy/network filtering next."
                )
            return (
                f"MANTIS could not unlock its higher reasoning layer (HTTP {status}). "
                "That usually means the saved intelligence key is wrong, expired, disabled, or copied with extra text. "
                "Create a fresh key, then use /save-key in this console."
                + (f"\nGateway detail: {details}" if details else "")
            )
        if status == 404:
            return (
                "MANTIS could not find the configured reasoning endpoint. "
                "Check the saved intelligence settings."
                + (f"\nGateway detail: {details}" if details else "")
            )
        if status == 429:
            return "MANTIS is being rate-limited. Wait a little and try again."
        return f"The MANTIS intelligence gateway returned HTTP {status}." + (f"\nGateway detail: {details}" if details else "")

    @staticmethod
    def _read_http_error(exc: urllib.error.HTTPError) -> str:
        try:
            return exc.read().decode("utf-8", errors="replace")
        except Exception:
            return ""

    @staticmethod
    def _extract_groq_error(body: str) -> str:
        if not body:
            return ""
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return body.strip()[:300]
        error = data.get("error") if isinstance(data, dict) else None
        if isinstance(error, dict):
            message = str(error.get("message") or "").strip()
            code = str(error.get("code") or "").strip()
            return f"{message} ({code})".strip() if code else message
        return str(data)[:300]

    def open_browser(self, lead: str) -> str:
        try:
            webbrowser.open(self.url, new=1)
            health = self.port_health()
            if health["open"]:
                return f"{lead} The local server is answering on port {self.port}."
            return f"{lead} I do not see the server answering yet, so give it a moment or ask me to check myself."
        except Exception as exc:  # pragma: no cover - defensive launcher path
            return f"I tried to open {self.url}, but Windows reported: {exc}"

    def self_check(self) -> str:
        health = self.port_health()
        log_summary = self.log_health()
        parts = [
            "Self-check complete.",
            f"Local URL: {self.url}",
            f"Port {self.port}: {'online' if health['open'] else 'not answering yet'}",
            f"HTTP check: {health['http']}",
            f"Log check: {log_summary}",
        ]
        if health["open"] and "error" not in log_summary.lower():
            parts.append("Verdict: runtime looks healthy from the launcher side.")
        else:
            parts.append("Verdict: I would keep the log open and try restart if the browser does not load.")
        return "\n".join(parts)

    def port_health(self) -> dict[str, object]:
        is_open = False
        try:
            with socket.create_connection(("127.0.0.1", self.port), timeout=1.2):
                is_open = True
        except OSError:
            is_open = False

        http_status = "not checked because the port is closed"
        if is_open:
            try:
                with urllib.request.urlopen(self.url, timeout=2.5) as response:
                    http_status = f"HTTP {response.status}"
            except urllib.error.HTTPError as exc:
                http_status = f"HTTP {exc.code}"
            except Exception as exc:  # pragma: no cover - depends on local runtime
                http_status = f"request failed: {exc}"

        return {"open": is_open, "http": http_status}

    def summarize_logs(self) -> str:
        if not self.log_file.exists():
            return "I do not see a launcher log yet. The server may still be starting."

        lines = self._tail(self.log_file, 25)
        if not lines:
            return "The launcher log exists, but it is empty right now."

        issues = [
            line.strip()
            for line in lines
            if re.search(r"\b(error|exception|traceback|failed|warning)\b", line, re.I)
        ]
        if issues:
            preview = "\n".join(f"- {line[:180]}" for line in issues[-5:])
            return f"I found these recent warning/error lines:\n{preview}"

        preview = "\n".join(line.rstrip() for line in lines[-8:])
        return f"No obvious recent errors. Latest log tail:\n{preview}"

    def log_health(self) -> str:
        if not self.log_file.exists():
            return "no log file yet"
        lines = self._tail(self.log_file, 80)
        issue_count = sum(
            1
            for line in lines
            if re.search(r"\b(error|exception|traceback|failed)\b", line, re.I)
        )
        if issue_count:
            return f"{issue_count} recent issue-looking line(s); ask 'log' for details"
        return "no recent error-looking lines"

    def small_talk(self, text: str) -> str:
        lowered = text.lower()
        if re.search(r"\b(hi|hello|hey|yo)\b", lowered):
            return "I am here. Talk to me like you would in this thread. What are we shaping next?"
        if "thank" in lowered:
            return "Any time. I like this version of MANTIS better too: less dashboard, more presence."
        if "who are you" in lowered or "what are you" in lowered:
            return (
                "I am MANTIS in the launcher: the little console presence that can talk with you, "
                "keep an eye on the app, and help you think through the work without turning everything into a menu."
            )
        if any(word in lowered for word in ("idea", "story", "chapter", "write", "brainstorm")):
            return (
                "Yes. Give me the rough version first, even if it is messy. "
                "I can help you turn it into something sharper without sanding all the life out of it."
            )
        if self.history:
            last_user = next((msg for speaker, msg in reversed(self.history) if speaker == "user"), "")
            if last_user:
                return (
                    "I am with you. I am holding the thread from what you just said, "
                    "but my higher reasoning layer is quiet right now. Say it one more way and I will help you shape it."
                )
        return (
            "I am listening. My deeper reasoning layer is quiet right now, but I can still stay with the thread. "
            "Tell me what you want this to feel like, and I will help steer it."
        )

    def help_text(self) -> str:
        return "\n".join(
            [
                "Command deck:",
                "/restart   Reopen the localhost window",
                "/status    Check the local runtime",
                "/logs      Read the latest server log lines",
                "/mantis    Check the intelligence core",
                "/memory    Show what launcher MANTIS has actually saved",
                "/learn X   Save a real launcher memory note",
                "/simulator Explain what learning/simulation can really do",
                "/save-key  Store a new intelligence key safely",
                "/clear     Redraw this console",
                "/exit      Close chat; MANTIS Studio keeps running",
                "",
                "Everything else is conversation. Just talk to me.",
            ]
        )

    def ai_status(self) -> str:
        if not self.groq_key:
            return (
                "MANTIS higher reasoning is offline. Use /save-key to restore it."
            )
        return (
            "MANTIS higher reasoning is online.\n"
            "Local runtime link: active\n"
            "Intelligence key: saved and hidden\n"
            f"Launcher memories: {len(self.memory.get('notes', []))}"
        )

    def remember(self, note: str) -> str:
        clean = re.sub(r"\s+", " ", note or "").strip()
        if not clean:
            return "Give me the thing to remember, like: /learn Call me Jeremy and keep replies direct."
        notes = self.memory.setdefault("notes", [])
        if not isinstance(notes, list):
            notes = []
            self.memory["notes"] = notes
        normalized = clean.lower()
        for item in notes:
            if isinstance(item, dict) and str(item.get("text", "")).strip().lower() == normalized:
                return "I already have that saved in launcher memory."
        notes.append({"text": clean, "created_at": _dt.datetime.now().isoformat(timespec="seconds")})
        self.memory["updated_at"] = _dt.datetime.now().isoformat(timespec="seconds")
        self._save_memory()
        return f"Saved to real launcher memory: {clean}"

    def memory_summary(self) -> str:
        notes = [item for item in self.memory.get("notes", []) if isinstance(item, dict)]
        if not notes:
            return "Launcher memory is empty. Use /learn followed by what you want me to remember."
        lines = ["Real launcher memory:"]
        for idx, item in enumerate(notes[-12:], start=1):
            lines.append(f"{idx}. {item.get('text', '')}")
        return "\n".join(lines)

    def simulator_truth(self) -> str:
        return (
            "The log showed me roleplaying a Matrix-style simulator. That was not real learning. "
            "Real MANTIS learning has to write to a local store or Knowledge Base.\n"
            "\n"
            "What I can do now:\n"
            "- /learn saves launcher memory that I will include in future chat context.\n"
            "- Knowledge Base in the app can import DOCX/TXT/Markdown and retrieve it for writing.\n"
            "- A real simulator should run scripted writing/canon scenarios and score MANTIS behavior.\n"
            "\n"
            "So yes, simulator is a good idea, but it needs to be command-backed and measurable."
        )

    def save_groq_key_interactive(self) -> str:
        if not sys.stdin.isatty():
            return "Key saving only works in the interactive launcher window."
        print("  MANTIS > Paste the new MANTIS intelligence key. It will be hidden while you type.")
        try:
            key = getpass.getpass("  MANTIS key > ").strip()
        except (EOFError, KeyboardInterrupt):
            return "Key update cancelled."
        if not key:
            return "Key update cancelled."
        return self._save_groq_key(key)

    def _save_groq_key(self, key: str) -> str:
        secrets_path = self.repo_root / ".streamlit" / "secrets.toml"
        secrets_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            existing = secrets_path.read_text(encoding="utf-8") if secrets_path.exists() else ""
            replacement = f'GROQ_API_KEY = "{self._toml_escape(key)}"'
            if re.search(r"(?m)^GROQ_API_KEY\s*=", existing):
                updated = re.sub(r'(?m)^GROQ_API_KEY\s*=.*$', replacement, existing)
            elif re.search(r"(?m)^groq_api_key\s*=", existing):
                updated = re.sub(r'(?m)^groq_api_key\s*=.*$', replacement, existing)
            else:
                spacer = "" if not existing or existing.endswith("\n") else "\n"
                updated = f"{existing}{spacer}{replacement}\n"
            secrets_path.write_text(updated, encoding="utf-8")
        except OSError as exc:
            return f"I could not save the key: {exc}"

        self._load_groq_settings()
        return (
            "Saved the MANTIS intelligence key and reloaded my higher reasoning layer. "
            "Use /mantis to confirm; the key stays hidden. "
            "If that key was pasted into the visible console, revoke it and save a fresh one."
        )

    def groq_fix_help(self) -> str:
        return (
            "MANTIS cannot unlock higher reasoning with the saved key. The fix is: revoke any exposed key, "
            "create a fresh one, restart this launcher chat, then use /save-key and paste it into "
            "the hidden prompt. After that, use /mantis and then just talk."
        )

    def _screen(self) -> None:
        if sys.stdin.isatty():
            os.system("cls" if os.name == "nt" else "clear")
        now = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print()
        self._print_banner()
        self._print_panel(
            "SESSION",
            [
                ("Runtime", self.url),
                ("Time", now),
                ("Mode", "Just talk. Use /help only when you want launcher commands."),
            ],
        )
        print()

    def _prompt(self) -> str:
        if not self.use_color:
            return "  You > "
        return "\033[96m  You > "

    def _reset_color(self) -> None:
        if self.use_color:
            print("\033[0m", end="")

    def _print_banner(self) -> None:
        if self.use_unicode:
            lines = [

                "╔═══════════════════════════════════════════════════════════════╗",
                "║                                                               ║",
                "║       ███╗   ███╗ █████╗ ███╗   ██╗████████╗██╗███████╗       ║",
                "║       ████╗ ████║██╔══██╗████╗  ██║╚══██╔══╝██║██╔════╝       ║",
                "║       ██ ████ ██║███████║██ ██╗ ██║   ██║   ██║██║            ║",
                "║       ██╔████╔██║███████║██╔╗██ ██║   ██║   ██║███████╗       ║",
                "║       ██║╚██╔╝██║██╔══██║██║╚██╗██║   ██║   ██║╚════██║       ║",
                "║       ██║ ╚═╝ ██║██║  ██║██║ ╚████║   ██║   ██║     ██║       ║",
                "║       ██║     ██║██║  ██║██║  ████║   ██║   ██║███████║       ║",
                "║       ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚══════╝       ║",
                "║         Modular AI Narrative Text Intelligence System         ║",
                "╚═══════════════════════════════════════════════════════════════╝",
            ]
        else:
            lines = [
                "+=======================================================+",
                "|                                                       |",
                "|       M   M   AAAAA   N   N  TTTTT  III   SSSSS       |",
                "|       MM MM   A   A   NN  N    T     I    S           |",
                "|       M M M   AAAAA   N N N    T     I    SSSSS       |",
                "|       M   M   A   A   N  NN    T     I        S       |",
                "|       M   M   A   A   N   N    T    III   SSSSS       |",
                "|                                                       |",
                "|     Modular AI Narrative Text Intelligence System     |",
                "+=======================================================+",
            ]
        for line in lines:
            print(self._color(line, "blue"))

    def _print_status_line(self, label: str, value: str) -> None:
        label_text = f"{label:<8}"
        print(f"  {self._color(label_text, 'cyan')} {value}")

    def _print_panel(self, title: str, rows: list[tuple[str, str]]) -> None:
        width = self.FRAME_WIDTH
        print(self._color("+" + "-" * (width - 2) + "+", "blue"))
        print(self._color("|", "blue") + f" {title:<{width - 4}}" + self._color("|", "blue"))
        print(self._color("|" + "-" * (width - 2) + "|", "blue"))
        for label, value in rows:
            value_width = width - 15
            wrapped = textwrap.wrap(value, width=value_width) or [""]
            for idx, chunk in enumerate(wrapped):
                row_label = label if idx == 0 else ""
                text = f" {row_label:<10} {chunk}"
                print(self._color("|", "blue") + f"{text:<{width - 2}}" + self._color("|", "blue"))
        print(self._color("+" + "-" * (width - 2) + "+", "blue"))

    def _boot_sequence(self) -> None:
        if not sys.stdin.isatty():
            return
        self._print_status_line("Boot", "Synchronizing console interface")
        print()
        self._print_status_line("Sync", self._bar(4, 24))
        self._sleep(0.08)
        self._print_status_line("Sync", self._bar(12, 24))
        self._sleep(0.08)
        self._print_status_line("Sync", self._bar(24, 24))
        print()
        self._print_status_line("Link", "Ready for conversation")
        print()

    def _thinking_pulse(self, label: str) -> None:
        if not sys.stdin.isatty():
            return
        for filled in (5, 11, 18, 24):
            print(f"\r  {self._color(label, 'cyan')} {self._bar(filled, 24)}", end="", flush=True)
            self._sleep(0.06)
        print()

    def _bar(self, filled: int, total: int) -> str:
        filled = max(0, min(filled, total))
        bar = ("█" * filled + "░" * (total - filled)) if self.use_unicode else ("#" * filled + "." * (total - filled))
        return self._color(f"[{bar}]", "blue")

    def _color(self, text: str, color: str) -> str:
        if not self.use_color:
            return text
        colors = {
            "blue": "\033[94m",
            "cyan": "\033[96m",
            "green": "\033[92m",
            "yellow": "\033[93m",
            "reset": "\033[0m",
        }
        return f"{colors.get(color, '')}{text}{colors['reset']}"

    @staticmethod
    def _sleep(seconds: float) -> None:
        try:
            import time

            time.sleep(seconds)
        except Exception:
            pass

    @staticmethod
    def _supports_unicode() -> bool:
        encoding = (sys.stdout.encoding or "").lower()
        return "utf" in encoding or "65001" in encoding

    def _connect_groq(self) -> None:
        if self.groq_key:
            self._print_status_line("Core", "Intelligence core online.")
            self._log_event("system", f"groq connected source={self.groq_key_source} model={self.groq_model}")
            print()
            return
        if not sys.stdin.isatty():
            return

        self._print_status_line("Core", "Intelligence core is offline.")
        self._print_status_line("Key", "Paste a MANTIS intelligence key, or press Enter for local mode.")
        try:
            key = getpass.getpass("  MANTIS key > ").strip()
        except (EOFError, KeyboardInterrupt):
            key = ""
        if key:
            self.groq_key = key
            self.groq_key_source = "session key"
            self._log_event("system", f"groq connected source={self.groq_key_source} model={self.groq_model}")
            self._print_status_line("Core", "Intelligence core online.")
        else:
            self._log_event("system", "running local conversation mode")
            self._print_status_line("Core", "Running local mode.")
        print()

    def _load_groq_settings(self) -> None:
        self.key_sources = []
        self.key_source_index = -1
        self.groq_key = ""
        self.groq_key_source = ""
        config = self._load_app_config()
        secrets = self._load_streamlit_secrets()

        self.groq_base_url = (
            os.getenv("GROQ_API_URL")
            or os.getenv("MANTIS_GROQ_API_URL")
            or str(config.get("groq_base_url") or "").strip()
            or "https://api.groq.com/openai/v1"
        )
        self.groq_model = (
            os.getenv("GROQ_MODEL")
            or os.getenv("MANTIS_GROQ_MODEL")
            or str(config.get("groq_model") or "").strip()
            or "llama3-8b-8192"
        )

        key_sources = [
            ("GROQ_API_KEY environment variable", os.getenv("GROQ_API_KEY")),
            ("MANTIS_GROQ_API_KEY environment variable", os.getenv("MANTIS_GROQ_API_KEY")),
            ("MANTIS saved app config", config.get("groq_api_key")),
            (".streamlit/secrets.toml groq_api_key", secrets.get("groq_api_key")),
            (".streamlit/secrets.toml GROQ_API_KEY", secrets.get("GROQ_API_KEY")),
            (".streamlit/secrets.toml [groq].api_key", self._nested_secret(secrets, "groq", "api_key")),
        ]
        for source, key in key_sources:
            cleaned = str(key or "").strip()
            if cleaned:
                self.key_sources.append(KeySource(source, cleaned))
        self._activate_next_key_source()

    def _load_memory(self) -> dict[str, object]:
        try:
            if self.memory_file.exists():
                data = json.loads(self.memory_file.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    data.setdefault("notes", [])
                    return data
        except (OSError, json.JSONDecodeError):
            pass
        return {"version": 1, "notes": []}

    def _save_memory(self) -> None:
        try:
            self.memory_file.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.memory_file.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(self.memory, indent=2), encoding="utf-8")
            tmp.replace(self.memory_file)
        except OSError:
            pass

    def _memory_prompt_context(self) -> str:
        notes = [item for item in self.memory.get("notes", []) if isinstance(item, dict)]
        if not notes:
            return "- No launcher memory has been saved yet."
        return "\n".join(f"- {item.get('text', '')}" for item in notes[-8:])

    def _load_app_config(self) -> dict[str, object]:
        config_path = Path(
            os.getenv("MANTIS_CONFIG_PATH")
            or self.repo_root / "projects" / ".mantis_config.json"
        )
        try:
            with config_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def _load_streamlit_secrets(self) -> dict[str, object]:
        if tomllib is None:
            return {}
        secrets_path = self.repo_root / ".streamlit" / "secrets.toml"
        try:
            with secrets_path.open("rb") as handle:
                data = tomllib.load(handle)
            return data if isinstance(data, dict) else {}
        except (OSError, tomllib.TOMLDecodeError):
            return {}

    @staticmethod
    def _nested_secret(data: dict[str, object], section: str, key: str) -> object:
        value = data.get(section)
        if isinstance(value, dict):
            return value.get(key)
        return None

    @staticmethod
    def _toml_escape(value: str) -> str:
        return value.replace("\\", "\\\\").replace('"', '\\"')

    @staticmethod
    def _tail(path: Path, limit: int) -> list[str]:
        try:
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                return handle.readlines()[-limit:]
        except OSError:
            return []

    def _log_event(self, speaker: str, message: str) -> None:
        try:
            self.chat_log_file.parent.mkdir(parents=True, exist_ok=True)
            timestamp = _dt.datetime.now().isoformat(timespec="seconds")
            safe_message = self._mask_secrets(message).replace("\r", "\\r")
            with self.chat_log_file.open("a", encoding="utf-8") as handle:
                for line in safe_message.splitlines() or [""]:
                    handle.write(f"{timestamp} [{speaker}] {line}\n")
        except OSError:
            pass

    @staticmethod
    def _mask_secrets(value: str) -> str:
        return re.sub(r"\bgsk_[A-Za-z0-9_-]{8,}\b", "gsk_***MASKED***", str(value))

    def _wrap(self, text: str) -> str:
        output: list[str] = []
        prefix = self._mantis_prefix()
        continuation = "           "
        for block in text.splitlines() or [""]:
            if not block:
                output.append("")
            elif block.startswith(("- ", "/")):
                output.extend(textwrap.wrap(block, width=92, initial_indent=prefix, subsequent_indent=continuation))
            elif block.endswith(":") and len(block) < 40:
                output.append(prefix + self._color(block, "cyan"))
            else:
                output.extend(textwrap.wrap(block, width=92, initial_indent=prefix, subsequent_indent=continuation))
        return "\n".join(output)

    def _mantis_prefix(self) -> str:
        if not self.use_color:
            return "  MANTIS > "
        return "\033[94m  MANTIS > \033[0m"

    @staticmethod
    def _asks_about_connection(text: str) -> bool:
        return bool(
            re.search(r"\b(connect|connected|internet|online|web|live data|real[- ]?time)\b", text)
            and re.search(r"\b(can|could|should|able|possible)\b", text)
        )

    @staticmethod
    def _extract_memory_request(text: str) -> str:
        clean = re.sub(r"\s+", " ", text or "").strip()
        patterns = [
            r"^(?:please\s+)?remember(?:\s+that)?\s+(.+)$",
            r"^(?:please\s+)?learn(?:\s+this)?[:\s]+(.+)$",
            r"^save\s+this\s+to\s+memory[:\s]+(.+)$",
        ]
        for pattern in patterns:
            match = re.search(pattern, clean, re.I)
            if match:
                note = match.group(1).strip()
                if note.lower() not in {"", "i guess", "now", "everything"}:
                    return note
        return ""

    @staticmethod
    def _asks_for_simulated_learning(text: str) -> bool:
        if "simulator" in text or "simulation" in text:
            return True
        if re.search(r"\b(start|keep|begin|continue)\s+learning\b", text):
            return True
        return bool("learning" in text and re.search(r"\b(matrix|progress|loading|autonomous|background)\b", text))

    @staticmethod
    def _user_is_claiming_creator_context(text: str) -> bool:
        return bool(
            re.search(r"\b(i|im|i'm|me)\b", text)
            and re.search(r"\b(created|made|built|building|developer|dev|creator|owner)\b", text)
            and re.search(r"\b(you|u|mantis|this)\b", text)
        )

    def _is_asking_about_groq_failure(self, text: str) -> bool:
        if not re.search(r"\b(why|fix|broken|forbidden|403|groq|key|api)\b", text):
            return False
        recent = "\n".join(
            content.lower()
            for speaker, content in self.history[-4:]
            if speaker == "mantis"
        )
        return "groq" in recent and ("403" in recent or "forbidden" in recent or "rejected" in recent)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MANTIS launcher chat assistant")
    parser.add_argument("--url", default="http://localhost:8501")
    parser.add_argument("--port", default="8501")
    parser.add_argument("--log-file", default="logs/launcher.log")
    parser.add_argument("--chat-log-file", default="logs/chat.log")
    parser.add_argument("--repo-root", default=".")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    return LauncherChat(args).run()


if __name__ == "__main__":
    raise SystemExit(main())
