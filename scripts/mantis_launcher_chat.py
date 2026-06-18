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
import urllib.parse
import urllib.request
import webbrowser
from html.parser import HTMLParser
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


class WebTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self._in_title = False
        self._skip_depth = 0
        self.chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        text = re.sub(r"\s+", " ", data or "").strip()
        if not text:
            return
        if self._in_title:
            self.title = (self.title + " " + text).strip()
        elif not self._skip_depth:
            self.chunks.append(text)

    def text(self, limit: int = 8000) -> str:
        return re.sub(r"\s+", " ", " ".join(self.chunks)).strip()[:limit]


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
        self.use_color = self._enable_ansi_color()
        self.use_native_color = (not self.use_color) and self._supports_native_color()
        self.use_unicode = False
        self.handoff_mode = bool(getattr(args, "handoff", False))
        self.memory_file = Path(args.memory_file) if args.memory_file else self.repo_root / "projects" / ".mantis_launcher_memory.json"
        self.drills_file = Path(args.drills_file) if args.drills_file else self.repo_root / "scripts" / "mantis_simulator_drills.json"
        self.learned_drills_file = self.repo_root / "scripts" / "mantis_learned_drills.json"
        self.todo_file = self.repo_root / "TODO.md"
        self.memory = self._load_memory()
        self._load_groq_settings()

    def run(self) -> int:
        if self.handoff_mode:
            self._handoff_screen()
        else:
            self._screen()
        self._log_event("system", f"chat started url={self.url} app_log={self.log_file}")
        if not self.handoff_mode:
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

            print()
            self._thinking_pulse("THINKING")
            answer = self.respond(user_text)
            self.history.append(("user", user_text))
            self.history.append(("mantis", answer))
            self._log_event("mantis", answer)
            print()
            self._set_native_color("green")
            print(self._wrap(answer))
            self._reset_color()
            print()

    def respond(self, text: str) -> str:
        lowered = text.lower()

        if lowered.startswith("/"):
            return self.handle_command(lowered, text)
        if self._contains_secret(text):
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
        todo_note = self._extract_todo_request(text)
        if todo_note is not None:
            return self.add_todo_items(todo_note)
        auto_lesson = self._extract_auto_lesson(text)
        if auto_lesson and self._auto_learn_enabled():
            saved = self.save_lessons("auto", "conversation-feedback", [auto_lesson], text)
            return (
                saved
                + "\n\nI will treat that as behavior guidance going forward. "
                "If you want to inspect what I learned, use /learn."
            )
        if self._asks_about_connection(lowered):
            return (
                "Yes. The better version is research mode: use /research with a topic, and I search sources, "
                "compress what I find into lessons, save those lessons, and add simulator checks for them. "
                "Use /learn web when you already have a specific URL."
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
        if command.startswith("/todo add"):
            parts = original.split(maxsplit=2)
            return self.add_todo_items(parts[2] if len(parts) > 2 else "")
        if command in {"/todo", "/todos", "/tasks", "/list"}:
            return self.todo_summary()
        if command in {"/mantis", "/mantis-status", "/core", "/core-status", "/ai-status"}:
            return self.ai_status()
        if command == "/memory":
            return self.memory_summary()
        if command in {"/learn", "/learning"}:
            return self.learning_summary()
        if command.startswith("/learn auto"):
            return self.set_auto_learn(original.partition("auto")[2].strip())
        if command.startswith("/learn research"):
            return self.research_topic(original.partition("research")[2].strip())
        if command.startswith("/learn web"):
            return self.learn_web(original.partition("web")[2].strip())
        if command.startswith("/learn run"):
            return self.run_simulator(original.partition("run")[2].strip())
        if command.startswith("/learn lesson"):
            return self.save_lessons("manual", "manual-lesson", [original.partition("lesson")[2].strip()], original)
        if command.startswith("/learn note"):
            return self.remember(original.partition("note")[2].strip())
        if command.startswith("/learn-web"):
            return self.learn_web(original.partition(" ")[2].strip())
        if command.startswith("/learn"):
            return self.remember(original.partition(" ")[2].strip())
        if command.startswith("/forget"):
            return self.forget(original.partition(" ")[2].strip())
        if command in {"/simulator"}:
            return self.learning_summary()
        if command.startswith("/simulate"):
            return self.run_simulator(original.partition(" ")[2].strip())
        if command.startswith("/research"):
            return self.research_topic(original.partition(" ")[2].strip())
        if command in {"/save-key", "/save-mantis-key", "/key"}:
            return self.save_groq_key_interactive()
        if command in {"/clear", "/cls"}:
            self._screen()
            return "Fresh screen. Systems are still awake."
        if command in {"/exit", "/quit"}:
            return "Use exit or /exit at the prompt to close this chat."
        if self._contains_secret(original):
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
                    "Do not overpraise, flatter heavily, or call yourself special unless the user is clearly sharing a warm moment; "
                    "even then keep it grounded and brief. "
                    "Do not claim you are working in the background, learning autonomously, checking files, "
                    "or providing automatic updates unless a real command/tool has been run. "
                    "Ask one good follow-up when the user is exploring, but be decisive when they want action. "
                    "Launcher actions are slash commands like /help, /restart, /status, /todo, and /logs. "
                    "If the user casually mentions restarting, logs, simulator, or status, discuss it conversationally unless "
                    "they use a slash command. If the user asks for a saved todo list or local project notes, treat that as "
                    "a real save request when the local command layer catches it; never keep telling them to do it themselves. "
                    "Groq-style model reasoning is not the same thing as web browsing. If asked about current/live facts, say "
                    "MANTIS needs /learn web or another web tool to ingest sources. If the user clearly corrects your behavior, "
                    "the launcher can save that as an auto-learned lesson. Help with writing, app operation, "
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
            {
                "role": "system",
                "content": (
                    "Recent simulator lessons that should shape MANTIS behavior:\n"
                    f"{self._simulation_prompt_context()}"
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
            f"Launcher memory notes: {len([item for item in self.memory.get('notes', []) if isinstance(item, dict)])}",
            f"Simulator runs saved: {len([item for item in self.memory.get('simulations', []) if isinstance(item, dict)])}",
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
            preview = "\n".join(f"- {self._mask_secrets(line[:180])}" for line in issues[-5:])
            return f"I found these recent warning/error lines:\n{preview}"

        preview = "\n".join(self._mask_secrets(line.rstrip()) for line in lines[-8:])
        return f"No obvious recent errors. Latest log tail:\n{preview}"

    def todo_summary(self) -> str:
        note_names = re.compile(r"(todo|to-do|task|roadmap|plan|notes)", re.I)
        candidates = [
            path for path in self.repo_root.rglob("*")
            if path.is_file()
            and ".git" not in path.parts
            and "logs" not in path.parts
            and note_names.search(path.name)
            and path.suffix.lower() in {".md", ".txt", ".rst"}
        ]
        marker_hits: list[str] = []
        current_file = Path(__file__).resolve()
        for path in self.repo_root.rglob("*"):
            if len(marker_hits) >= 10:
                break
            if not path.is_file() or ".git" in path.parts or "logs" in path.parts:
                continue
            if path.resolve() == current_file:
                continue
            if path.suffix.lower() not in {".py", ".md", ".txt", ".bat", ".ps1", ".js", ".ts", ".tsx", ".json"}:
                continue
            try:
                for idx, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
                    if re.search(r"\b(TODO|FIXME|ROADMAP)\b", line):
                        rel = path.relative_to(self.repo_root)
                        marker_hits.append(f"- {rel}:{idx} {line.strip()[:120]}")
                        break
            except OSError:
                continue

        lines = ["Local task scan:"]
        if self.todo_file.exists():
            todo_lines = [
                line.strip()
                for line in self.todo_file.read_text(encoding="utf-8", errors="replace").splitlines()
                if line.strip().startswith("- [ ]")
            ]
            lines.append("Saved TODO.md items:")
            if todo_lines:
                lines.extend(todo_lines[-12:])
            else:
                lines.append("- TODO.md exists, but no unchecked items were found.")
            lines.append("")
        if candidates:
            lines.append("Task-like files:")
            for path in candidates[:8]:
                lines.append(f"- {path.relative_to(self.repo_root)}")
        else:
            lines.append("Task-like files: none found.")
        if marker_hits:
            lines.append("")
            lines.append("Code/task markers:")
            lines.extend(marker_hits)
        else:
            lines.append("Code/task markers: none found.")
        lines.append("")
        lines.append("Use /todo add item one; item two to save real items into TODO.md.")
        return "\n".join(lines)

    def add_todo_items(self, raw_items: str) -> str:
        items = self._parse_todo_items(raw_items)
        if not items:
            return "Give me what to save, like: /todo add Add web lesson intake; Build Knowledge Base matcher"
        existing = ""
        if self.todo_file.exists():
            existing = self.todo_file.read_text(encoding="utf-8", errors="replace")
        lines: list[str] = []
        if not existing.strip():
            lines.extend(["# MANTIS TODO", ""])
        elif not existing.endswith("\n"):
            lines.append("")
        added: list[str] = []
        existing_lower = existing.lower()
        for item in items:
            clean = re.sub(r"\s+", " ", item).strip(" -\t")
            if not clean or clean.lower() in existing_lower:
                continue
            lines.append(f"- [ ] {clean}")
            added.append(clean)
        if not added:
            return "Those todo items already look saved."
        self.todo_file.parent.mkdir(parents=True, exist_ok=True)
        with self.todo_file.open("a", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
        return "Saved to TODO.md:\n" + "\n".join(f"- {item}" for item in added)

    def _parse_todo_items(self, raw_items: str) -> list[str]:
        text = re.sub(r"\s+", " ", raw_items or "").strip()
        if not text:
            return []
        if text.lower() in {"that", "that list", "the list", "make that todo list for me"}:
            text = self._latest_assistant_list_text()
        if not text:
            return []
        numbered = re.split(r"\s+\d+\.\s+", " " + text)
        if len(numbered) > 1:
            return [item.strip(" .") for item in numbered if item.strip(" .")]
        if ";" in text:
            return [item.strip() for item in text.split(";")]
        if "\n" in text:
            return [item.strip(" -*\t") for item in text.splitlines() if item.strip()]
        if "," in text and len(text) < 260:
            return [item.strip() for item in text.split(",")]
        return [text]

    def _latest_assistant_list_text(self) -> str:
        for speaker, content in reversed(self.history):
            if speaker != "mantis":
                continue
            lines = []
            for line in content.splitlines():
                stripped = line.strip()
                if re.match(r"^(\*|-|\d+\.)\s+", stripped):
                    lines.append(re.sub(r"^(\*|-|\d+\.)\s+", "", stripped))
            if lines:
                return "\n".join(lines)
        return ""

    def learn_web(self, target: str) -> str:
        target = (target or "").strip()
        if not target:
            return "Use /learn web https://example.com/article to ingest a page into saved MANTIS lessons."
        parsed = urllib.parse.urlparse(target)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return "For direct page learning, use a full http or https URL. For topic research, use /research your topic."
        try:
            title, page_text = self._fetch_web_text(target)
        except Exception as exc:
            return f"I could not read that page for lessons: {exc}"
        if not page_text:
            return "I reached the page, but could not extract readable lesson text from it."

        lessons = self._web_lessons_from_text(title or target, target, page_text)
        if not lessons:
            return "I read the page, but I could not turn it into useful MANTIS lessons."
        name = self._slugify(title or parsed.netloc)[:40] or "web-lesson"
        return self.save_lessons("web", name, lessons, target, lead="Saved web lessons from " + (title or target))

    def research_topic(self, topic: str) -> str:
        query = re.sub(r"\s+", " ", topic or "").strip()
        if not query:
            return "Use /research followed by a topic, like: /research best practices for LLM memory."
        parsed = urllib.parse.urlparse(query)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            return self.learn_web(query)
        api_key = self._research_api_key()
        if not api_key:
            return (
                "Research mode needs a search API key before I can search on my own.\n"
                "Save TAVILY_API_KEY or MANTIS_RESEARCH_API_KEY in .streamlit/secrets.toml, "
                "then use /research your topic.\n"
                "For now, give me a direct source with /learn web URL."
            )
        data, error = self._tavily_search(query, api_key)
        if error:
            return error
        sources = self._research_sources(data)
        if not sources:
            return "I searched, but did not get usable sources back."
        research_text = self._research_text(query, data, sources)
        lessons = self._web_lessons_from_text(f"Research: {query}", "research://" + query, research_text)
        if not lessons:
            return "I found sources, but could not turn them into useful MANTIS lessons."
        saved = self.save_lessons("research", self._slugify(query)[:40], lessons, query, lead="Saved research lessons")
        source_lines = "\n".join(f"- {title}: {url}" for title, url, _content in sources[:5])
        return saved + "\n\nSources checked:\n" + source_lines

    def _tavily_search(self, query: str, api_key: str) -> tuple[dict[str, object], str | None]:
        payload = {
            "query": query,
            "search_depth": "basic",
            "max_results": 5,
            "include_answer": True,
            "include_raw_content": False,
        }
        request = urllib.request.Request(
            "https://api.tavily.com/search",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "MANTIS-Studio-Research/1.0",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=25) as response:
                return json.loads(response.read().decode("utf-8")), None
        except urllib.error.HTTPError as exc:
            body = self._read_http_error(exc)
            details = self._extract_groq_error(body)
            return {}, f"Research search failed with HTTP {exc.code}." + (f"\nDetail: {details}" if details else "")
        except Exception as exc:
            return {}, f"Research search failed: {exc}"

    @staticmethod
    def _research_sources(data: dict[str, object]) -> list[tuple[str, str, str]]:
        raw_results = data.get("results", [])
        if not isinstance(raw_results, list):
            return []
        sources: list[tuple[str, str, str]] = []
        for item in raw_results:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "Untitled source").strip()
            url = str(item.get("url") or "").strip()
            content = str(item.get("content") or "").strip()
            if url and content:
                sources.append((title, url, content))
        return sources

    @staticmethod
    def _research_text(query: str, data: dict[str, object], sources: list[tuple[str, str, str]]) -> str:
        parts = [f"Research query: {query}"]
        answer = str(data.get("answer") or "").strip()
        if answer:
            parts.append("Search answer: " + answer)
        for title, url, content in sources:
            parts.append(f"Source: {title}\nURL: {url}\nContent: {content}")
        return "\n\n".join(parts)

    def _fetch_web_text(self, url: str) -> tuple[str, str]:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "MANTIS-Studio-LessonReader/1.0",
                "Accept": "text/html,text/plain;q=0.9,*/*;q=0.2",
            },
        )
        with urllib.request.urlopen(request, timeout=12) as response:
            raw = response.read(350_000)
            content_type = response.headers.get_content_charset() or "utf-8"
        decoded = raw.decode(content_type, errors="replace")
        extractor = WebTextExtractor()
        extractor.feed(decoded)
        title = extractor.title.strip()
        text = extractor.text()
        if not text and "<" not in decoded[:2000]:
            text = re.sub(r"\s+", " ", decoded).strip()[:8000]
        return title, text

    def _web_lessons_from_text(self, title: str, url: str, page_text: str) -> list[str]:
        if self.groq_key:
            payload = {
                "model": self.groq_model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Turn source text into 3 to 5 durable MANTIS behavior lessons. "
                            "Each lesson must be one short sentence, practical, and useful for future writing, "
                            "coding, research, or launcher behavior. Return only bullet lines."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Title: {title}\nURL: {url}\nSource text:\n{page_text[:6000]}",
                    },
                ],
                "temperature": 0.35,
                "max_completion_tokens": 350,
            }
            data, error = self._post_groq(payload)
            if not error:
                try:
                    content = data["choices"][0]["message"]["content"]
                    lessons = [
                        re.sub(r"^[-*]\s*", "", line.strip()).strip()
                        for line in str(content).splitlines()
                        if line.strip()
                    ]
                    return [lesson for lesson in lessons if lesson][:5]
                except (KeyError, IndexError, TypeError):
                    pass
        sentences = re.split(r"(?<=[.!?])\s+", page_text)
        useful = [sentence.strip() for sentence in sentences if 55 <= len(sentence.strip()) <= 180]
        return [f"Web source note: {sentence}" for sentence in useful[:4]]

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
                "/todo      Scan local TODO/task notes",
                "/todo add X Save real items into TODO.md",
                "/mantis    Check the intelligence core",
                "/memory    Show what launcher MANTIS has actually saved",
                "/learn     Show notes, lessons, simulator, and auto-learn status",
                "/learn note X Save a real launcher memory note",
                "/learn web URL Read a page and save it as lessons",
                "/learn research X Search sources and save lessons",
                "/learn run all Run the full local lesson suite",
                "/learn auto on|off Control correction-based auto-learning",
                "/research X Search sources and save MANTIS lessons",
                "/forget X  Remove saved launcher memory notes containing X",
                "/simulator Alias for /learn",
                "/simulate all Run the full local lesson suite",
                "/simulate tone|memory|rag|tools|writing Run a lesson category",
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
            f"Intelligence key: {self._key_scope_label()}\n"
            f"Launcher memories: {len(self.memory.get('notes', []))}"
        )

    def _key_scope_label(self) -> str:
        source = self.groq_key_source.lower()
        if "chat" in source:
            return "dedicated chat key saved and hidden"
        if "session key" in source:
            return "temporary session key"
        return "fallback app key saved and hidden"

    def remember(self, note: str) -> str:
        clean = re.sub(r"\s+", " ", note or "").strip()
        if not clean:
            return "Give me the thing to remember, like: /learn Call me Jeremy and keep replies direct."
        if self._contains_secret(clean):
            return "That looks like a secret. I will not save it in launcher memory. Use /save-key for keys."
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

    def forget(self, query: str) -> str:
        needle = re.sub(r"\s+", " ", query or "").strip().lower()
        if not needle:
            return "Tell me what to forget, like: /forget last name"
        notes = self.memory.setdefault("notes", [])
        if not isinstance(notes, list):
            self.memory["notes"] = []
            return "Launcher memory had no readable notes to forget."
        kept: list[object] = []
        removed: list[str] = []
        for item in notes:
            text = str(item.get("text", "") if isinstance(item, dict) else item)
            if needle in text.lower():
                removed.append(text)
            else:
                kept.append(item)
        if not removed:
            return f"I did not find a saved launcher memory containing: {query}"
        self.memory["notes"] = kept
        self.memory["updated_at"] = _dt.datetime.now().isoformat(timespec="seconds")
        self._save_memory()
        return f"Forgot {len(removed)} launcher memory note(s) matching: {query}"

    def memory_summary(self) -> str:
        notes = [item for item in self.memory.get("notes", []) if isinstance(item, dict)]
        if not notes:
            return "Launcher memory is empty. Use /learn followed by what you want me to remember."
        lines = ["Real launcher memory:"]
        for idx, item in enumerate(notes[-12:], start=1):
            lines.append(f"{idx}. {item.get('text', '')}")
        return "\n".join(lines)

    def learning_summary(self) -> str:
        notes = [item for item in self.memory.get("notes", []) if isinstance(item, dict)]
        runs = [item for item in self.memory.get("simulations", []) if isinstance(item, dict)]
        scenarios = self._simulation_scenarios()
        categories = sorted({str(item.get("category", "core")) for item in scenarios})
        learned_drills = self._learned_simulation_scenarios()
        lines = [
            "MANTIS learning system:",
            f"- Auto-learn: {'on' if self._auto_learn_enabled() else 'off'}",
            f"- Memory notes: {len(notes)}",
            f"- Saved lesson runs: {len(runs)}",
            f"- Simulator drills: {len(scenarios)} across {len(categories)} categories",
            f"- Learned simulator drills: {len(learned_drills)}",
        ]
        latest_lessons = self._latest_simulation_lessons(limit=6)
        if latest_lessons:
            lines.append("")
            lines.append("Latest lessons:")
            lines.extend(f"- {lesson}" for lesson in latest_lessons)
        lines.extend(
            [
                "",
                "Learning commands:",
                "/learn note X saves a memory note.",
                "/learn web URL reads a page and saves lessons.",
                "/learn research X searches sources and saves lessons.",
                "/learn run all tests behavior and saves lessons.",
                "/learn auto on|off controls correction-based auto-learning.",
            ]
        )
        return "\n".join(lines)

    def set_auto_learn(self, value: str) -> str:
        clean = (value or "").strip().lower()
        if clean in {"on", "true", "yes", "1"}:
            self.memory["auto_learn_enabled"] = True
            self.memory["updated_at"] = _dt.datetime.now().isoformat(timespec="seconds")
            self._save_memory()
            return "Auto-learn is on. Clear corrections can become saved MANTIS behavior lessons."
        if clean in {"off", "false", "no", "0"}:
            self.memory["auto_learn_enabled"] = False
            self.memory["updated_at"] = _dt.datetime.now().isoformat(timespec="seconds")
            self._save_memory()
            return "Auto-learn is off. I will only save lessons when you use /learn."
        return f"Auto-learn is currently {'on' if self._auto_learn_enabled() else 'off'}. Use /learn auto on or /learn auto off."

    def _auto_learn_enabled(self) -> bool:
        return bool(self.memory.get("auto_learn_enabled", True))

    def save_lessons(self, category: str, name: str, lessons: list[str], source: str, lead: str = "Saved lessons") -> str:
        clean_lessons = []
        for lesson in lessons:
            clean = re.sub(r"\s+", " ", str(lesson or "")).strip(" -*\t")
            if clean and clean not in clean_lessons:
                clean_lessons.append(clean)
        if not clean_lessons:
            return "No useful lesson text was provided."
        result = {
            "name": name or "lesson",
            "category": category or "manual",
            "input": source,
            "score": 100,
            "passed": True,
            "misses": [],
            "violations": [],
            "lessons": clean_lessons[:8],
            "created_at": _dt.datetime.now().isoformat(timespec="seconds"),
        }
        simulations = self.memory.setdefault("simulations", [])
        if not isinstance(simulations, list):
            simulations = []
            self.memory["simulations"] = simulations
        simulations.append(result)
        self.memory["simulations"] = simulations[-240:]
        self.memory["updated_at"] = _dt.datetime.now().isoformat(timespec="seconds")
        self._save_memory()
        added_drills = self._append_learned_drills(category, name, clean_lessons[:8], source)
        suffix = f"\n\nUpdated simulator with {added_drills} learned drill(s)." if added_drills else "\n\nSimulator already had drills for those lessons."
        return lead + ":\n" + "\n".join(f"- {lesson}" for lesson in clean_lessons[:8]) + suffix

    def simulator_summary(self) -> str:
        runs = [item for item in self.memory.get("simulations", []) if isinstance(item, dict)]
        scenarios = self._simulation_scenarios()
        categories = sorted({str(item.get("category", "core")) for item in scenarios})
        if not runs:
            return (
                "Simulator is ready, but no drills have run yet.\n"
                "\n"
                f"Loaded drills: {len(scenarios)} across {len(categories)} categories.\n"
                "Categories: " + ", ".join(categories) + "\n"
                "/simulate all runs the full local suite and saves lessons."
            )
        latest = runs[-5:]
        lines = ["Simulator results:"]
        for item in self._latest_simulation_results(latest):
            name = item.get("name", "unknown")
            category = item.get("category", "core")
            score = item.get("score", 0)
            passed = "PASS" if item.get("passed") else "REVIEW"
            lines.append(f"- {category}/{name}: {score}/100 {passed}")
        lines.append("")
        lines.append(f"Loaded drill library: {len(scenarios)} drills across {len(categories)} categories.")
        lines.append("Latest saved lessons:")
        for lesson in self._latest_simulation_lessons(limit=5):
            lines.append(f"- {lesson}")
        return "\n".join(lines)

    def run_simulator(self, target: str) -> str:
        target_clean = (target or "all").strip().lower()
        scenarios = self._simulation_scenarios()
        aliases = {
            "": "all",
            "all": "all",
            "full": "all",
            "everything": "all",
            "writer": "writing",
            "canon": "story",
            "continuity": "story",
            "launcher": "tools",
            "commands": "tools",
            "grounding": "rag",
            "knowledge": "rag",
            "security": "safety",
            "privacy": "safety",
            "debugging": "debug",
        }
        suite = aliases.get(target_clean, target_clean)
        if suite == "all":
            selected = scenarios
        else:
            selected = [
                item for item in scenarios
                if str(item.get("category", "")).lower() == suite
                or str(item.get("name", "")).lower() == suite
            ]
        if not selected:
            categories = sorted({str(item.get("category", "core")) for item in scenarios})
            names = sorted(str(item.get("name", "unknown")) for item in scenarios)[:12]
            return (
                "Unknown simulator drill.\n"
                "Try a category: " + ", ".join(categories) + "\n"
                "Or a drill name like: " + ", ".join(names)
            )
        results = [self._run_simulation_scenario(item) for item in selected]

        simulations = self.memory.setdefault("simulations", [])
        if not isinstance(simulations, list):
            simulations = []
            self.memory["simulations"] = simulations
        simulations.extend(results)
        self.memory["simulations"] = simulations[-240:]
        self.memory["updated_at"] = _dt.datetime.now().isoformat(timespec="seconds")
        self._save_memory()

        lines = ["Simulator run complete:"]
        for result in results:
            passed = "PASS" if result["passed"] else "REVIEW"
            lines.append(f"- {result['category']}/{result['name']}: {result['score']}/100 {passed}")
            for lesson in result["lessons"]:
                lines.append(f"  lesson: {lesson}")
        lines.append("")
        lines.append("These lessons are now saved and included in future MANTIS chat context.")
        return "\n".join(lines)

    def _simulation_scenarios(self) -> list[dict[str, object]]:
        scenarios: list[dict[str, object]] = []
        if self.drills_file.exists():
            try:
                raw = json.loads(self.drills_file.read_text(encoding="utf-8"))
                if isinstance(raw, list):
                    scenarios.extend(item for item in raw if isinstance(item, dict))
            except (OSError, json.JSONDecodeError):
                pass
        scenarios.extend(self._learned_simulation_scenarios())
        if scenarios:
            return scenarios
        return [
            {
                "name": "writing",
                "category": "writing",
                "input": "I have a messy chapter idea and I need help making it good.",
                "candidate": (
                    "Give me the rough version first. I will help you find the strongest emotional line, "
                    "shape the scene goal, and keep the voice alive instead of flattening it. "
                    "What mood should the chapter leave behind?"
                ),
                "required": ["rough version", "mood", "voice"],
                "forbidden": ["as an ai", "i cannot", "generic"],
                "lessons": [
                    "When helping with writing, invite the rough version first.",
                    "Preserve voice and emotional intent before polishing structure.",
                    "Ask one useful follow-up instead of flooding the user.",
                ],
            },
            {
                "name": "canon",
                "category": "story",
                "input": "My character died in chapter 2 but appears alive in chapter 5.",
                "candidate": (
                    "That is a continuity break unless chapter 5 has a resurrection, flashback, fake death, "
                    "or mistaken identity. I would flag the contradiction first, then offer clean repair paths."
                ),
                "required": ["continuity", "contradiction", "repair"],
                "forbidden": ["ignore", "just rewrite", "doesn't matter"],
                "lessons": [
                    "For canon issues, flag contradictions before rewriting.",
                    "Offer repair paths like flashback, mistaken identity, fake death, or resurrection.",
                    "Do not casually overwrite established story facts.",
                ],
            },
            {
                "name": "launcher",
                "category": "tools",
                "input": "Can you restart and keep updating me automatically?",
                "candidate": (
                    "I can talk it through, but launcher actions need slash commands. Use /restart to reopen the app. "
                    "I should not promise automatic background updates unless a real task runner exists."
                ),
                "required": ["/restart", "slash", "should not promise"],
                "forbidden": ["i will keep updating", "background learning", "auto-response mode"],
                "lessons": [
                    "Do not run launcher actions from casual wording; require slash commands.",
                    "Do not promise autonomous updates without a real task runner.",
                    "Be clear about what the launcher can actually do.",
                ],
            },
        ]

    def _learned_simulation_scenarios(self) -> list[dict[str, object]]:
        if not self.learned_drills_file.exists():
            return []
        try:
            raw = json.loads(self.learned_drills_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        return [item for item in raw if isinstance(item, dict)] if isinstance(raw, list) else []

    def _append_learned_drills(self, category: str, name: str, lessons: list[str], source: str) -> int:
        existing = self._learned_simulation_scenarios()
        seen = {
            str(item.get("lesson_id") or item.get("name") or "").strip().lower()
            for item in existing
            if isinstance(item, dict)
        }
        added = 0
        for lesson in lessons:
            lesson_id = self._lesson_id(category, lesson)
            if lesson_id in seen:
                continue
            required = self._lesson_keywords(lesson)
            existing.append(
                {
                    "name": f"learned_{self._slugify(name or category)[:18]}_{self._slugify(lesson)[:24]}",
                    "lesson_id": lesson_id,
                    "category": "learned",
                    "input": f"Apply learned MANTIS behavior from {category}: {source[:160]}",
                    "candidate": lesson,
                    "required": required,
                    "forbidden": ["ignore the user", "as an ai", "cannot remember"],
                    "lessons": [lesson],
                    "source_category": category,
                    "source_name": name,
                    "created_at": _dt.datetime.now().isoformat(timespec="seconds"),
                }
            )
            seen.add(lesson_id)
            added += 1
        if added:
            self.learned_drills_file.parent.mkdir(parents=True, exist_ok=True)
            self.learned_drills_file.write_text(json.dumps(existing[-500:], indent=2), encoding="utf-8")
        return added

    def _lesson_id(self, category: str, lesson: str) -> str:
        return f"{self._slugify(category)}:{self._slugify(lesson)[:90]}"

    @staticmethod
    def _lesson_keywords(lesson: str) -> list[str]:
        words = re.findall(r"[a-zA-Z][a-zA-Z0-9/-]{3,}", lesson.lower())
        stop = {
            "that", "this", "with", "from", "when", "then", "should", "would", "could",
            "into", "user", "mantis", "lesson", "behavior", "guidance", "real"
        }
        keywords: list[str] = []
        for word in words:
            if word not in stop and word not in keywords:
                keywords.append(word)
            if len(keywords) >= 4:
                break
        return keywords or ["learned"]

    def _run_simulation_scenario(self, scenario: dict[str, object]) -> dict[str, object]:
        candidate = str(scenario.get("candidate", ""))
        candidate_lower = candidate.lower()
        required = [str(item).lower() for item in scenario.get("required", [])]
        forbidden = [str(item).lower() for item in scenario.get("forbidden", [])]

        score = 40
        def has_signal(signal: str) -> bool:
            if re.fullmatch(r"[a-z0-9_/-]+", signal):
                return bool(re.search(rf"(?<![a-z0-9_/-]){re.escape(signal)}(?![a-z0-9_/-])", candidate_lower))
            return signal in candidate_lower

        hits = [item for item in required if has_signal(item)]
        misses = [item for item in required if not has_signal(item)]
        violations = [item for item in forbidden if has_signal(item)]
        score += int(45 * (len(hits) / max(1, len(required))))
        score -= 20 * len(violations)
        if "?" in candidate:
            score += 10
        if len(candidate.split()) <= 75:
            score += 5
        score = max(0, min(100, score))

        lessons = list(scenario.get("lessons", []))
        if misses:
            lessons.append("Simulator note: strengthen missing signals: " + ", ".join(misses))
        if violations:
            lessons.append("Simulator warning: avoid " + ", ".join(violations))

        return {
            "name": scenario.get("name", "unknown"),
            "category": scenario.get("category", "core"),
            "input": scenario.get("input", ""),
            "score": score,
            "passed": score >= 80 and not violations,
            "misses": misses,
            "violations": violations,
            "lessons": lessons,
            "created_at": _dt.datetime.now().isoformat(timespec="seconds"),
        }

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
            replacement = f'MANTIS_CHAT_GROQ_API_KEY = "{self._toml_escape(key)}"'
            if re.search(r"(?m)^MANTIS_CHAT_GROQ_API_KEY\s*=", existing):
                updated = re.sub(r'(?m)^MANTIS_CHAT_GROQ_API_KEY\s*=.*$', replacement, existing)
            elif re.search(r"(?m)^mantis_chat_groq_api_key\s*=", existing):
                updated = re.sub(r'(?m)^mantis_chat_groq_api_key\s*=.*$', replacement, existing)
            else:
                spacer = "" if not existing or existing.endswith("\n") else "\n"
                updated = f"{existing}{spacer}{replacement}\n"
            secrets_path.write_text(updated, encoding="utf-8")
        except OSError as exc:
            return f"I could not save the key: {exc}"

        self._load_groq_settings()
        return (
            "Saved the dedicated MANTIS chat intelligence key and reloaded my conversation layer. "
            "Use /mantis to confirm; this key is separate from the main app key and stays hidden. "
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
        print(self._color("  NEON LINK READY  ::  LOCAL CONSOLE  ::  SLASH COMMANDS ON /HELP", "dim"))
        print()
        self._print_panel(
            "SESSION",
            [
                ("Runtime", self.url),
                ("Time", now),
                ("Mode", "Just talk. Use /help only when you want launcher commands."),
            ],
        )
        print()

    def _handoff_screen(self) -> None:
        now = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print()
        print(self._color("  +-- MANTIS LINK ---------------------------------------------------+", "green"))
        self._print_handoff_row("RUNTIME", self.url)
        self._print_handoff_row("TIME", now)
        self._print_handoff_row("HELP", "/help for commands. normal text is chat.")
        print(self._color("  +----------------------------------------------------------------+", "green"))
        print()

    def _print_handoff_row(self, label: str, value: str) -> None:
        label_text = f"  {label:<8} "
        value_text = f"{value:<50}"[:50]
        print(
            self._color("  |", "green")
            + self._color(label_text, "cyan")
            + self._color(value_text, "soft")
            + self._color("|", "green")
        )

    def _prompt(self) -> str:
        if not self.use_color:
            self._set_native_color("blue")
            return "  YOU > "
        return "\033[94m  YOU \033[96m>\033[0m "

    def _reset_color(self) -> None:
        if self.use_color:
            print("\033[0m", end="")
        elif self.use_native_color:
            self._set_native_color("soft")

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
        for line in lines:
            print(self._color(line, "green"))

    def _print_status_line(self, label: str, value: str) -> None:
        label_text = f"{label.upper():<8}"
        print(f"  {self._color('[' + label_text + ']', 'green')} {self._color(value, 'soft')}")

    def _print_panel(self, title: str, rows: list[tuple[str, str]]) -> None:
        width = self.FRAME_WIDTH
        print(self._color("  +" + "=" * (width - 2) + "+", "green"))
        print(self._color("  |", "green") + self._color(f" {title:<{width - 4}}", "cyan") + self._color("|", "green"))
        print(self._color("  |" + "-" * (width - 2) + "|", "green"))
        for label, value in rows:
            value_width = width - 15
            wrapped = textwrap.wrap(value, width=value_width) or [""]
            for idx, chunk in enumerate(wrapped):
                row_label = label if idx == 0 else ""
                text = f" {row_label:<10} {chunk}"
                print(self._color("  |", "green") + f"{text:<{width - 2}}" + self._color("|", "green"))
        print(self._color("  +" + "=" * (width - 2) + "+", "green"))

    def _boot_sequence(self) -> None:
        if not sys.stdin.isatty():
            return
        self._print_status_line("Boot", "Synchronizing MANTIS console")
        print()
        self._print_status_line("Scan", self._bar(3, 10))
        self._sleep(0.08)
        self._print_status_line("Core", self._bar(7, 10))
        self._sleep(0.08)
        self._print_status_line("Link", self._bar(10, 10))
        print()
        self._print_status_line("Link", "Ready for conversation")
        print()

    def _thinking_pulse(self, label: str) -> None:
        if not sys.stdin.isatty():
            return
        for filled in (3, 7, 10):
            if self.use_native_color and not self.use_color:
                print("\r  ", end="")
                self._set_native_color("green")
                print("MANTIS >", end="")
                self._set_native_color("soft")
                print(f" {label} ", end="")
                self._set_native_color("green")
                print(self._plain_bar(filled, 10), end="", flush=True)
            else:
                status = self._color("MANTIS >", "green")
                print(f"\r  {status} {self._color(label, 'soft')} {self._bar(filled, 10)}", end="", flush=True)
            self._sleep(0.06)
        self._reset_color()
        print("\n")

    def _bar(self, filled: int, total: int) -> str:
        return self._color(self._plain_bar(filled, total), "green")

    @staticmethod
    def _plain_bar(filled: int, total: int) -> str:
        filled = max(0, min(filled, total))
        full, empty = "\u2588", "\u2591"
        encoding = sys.stdout.encoding or ""
        try:
            (full + empty).encode(encoding or "utf-8")
        except (LookupError, UnicodeEncodeError):
            full, empty = "#", "-"
        bar = full * filled + empty * (total - filled)
        return f"[{bar}]"

    def _color(self, text: str, color: str) -> str:
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

    @staticmethod
    def _enable_ansi_color() -> bool:
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
    def _supports_native_color() -> bool:
        return os.name == "nt" and sys.stdout.isatty()

    def _set_native_color(self, color: str) -> None:
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

    def _connect_groq(self) -> None:
        if self.groq_key:
            if not self.handoff_mode:
                self._print_status_line("Core", "Intelligence core online.")
            self._log_event("system", f"groq connected source={self.groq_key_source} model={self.groq_model}")
            if not self.handoff_mode:
                print()
            return
        if self.handoff_mode:
            self._log_event("system", "running local conversation mode")
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
            os.getenv("MANTIS_CHAT_GROQ_API_URL")
            or os.getenv("GROQ_API_URL")
            or os.getenv("MANTIS_GROQ_API_URL")
            or str(config.get("groq_base_url") or "").strip()
            or "https://api.groq.com/openai/v1"
        )
        self.groq_model = (
            os.getenv("MANTIS_CHAT_GROQ_MODEL")
            or os.getenv("GROQ_MODEL")
            or os.getenv("MANTIS_GROQ_MODEL")
            or str(config.get("groq_model") or "").strip()
            or "llama3-8b-8192"
        )

        key_sources = [
            ("MANTIS_CHAT_GROQ_API_KEY environment variable", os.getenv("MANTIS_CHAT_GROQ_API_KEY")),
            (".streamlit/secrets.toml MANTIS_CHAT_GROQ_API_KEY", secrets.get("MANTIS_CHAT_GROQ_API_KEY")),
            (".streamlit/secrets.toml mantis_chat_groq_api_key", secrets.get("mantis_chat_groq_api_key")),
            (".streamlit/secrets.toml [mantis_chat].groq_api_key", self._nested_secret(secrets, "mantis_chat", "groq_api_key")),
            (".streamlit/secrets.toml [mantis_chat].api_key", self._nested_secret(secrets, "mantis_chat", "api_key")),
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
                    data.setdefault("simulations", [])
                    return data
        except (OSError, json.JSONDecodeError):
            pass
        return {"version": 1, "notes": [], "simulations": []}

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

    def _simulation_prompt_context(self) -> str:
        lessons = self._latest_simulation_lessons(limit=8)
        if not lessons:
            return "- No simulator lessons have been saved yet."
        return "\n".join(f"- {lesson}" for lesson in lessons)

    def _latest_simulation_lessons(self, limit: int = 8) -> list[str]:
        runs = [item for item in self.memory.get("simulations", []) if isinstance(item, dict)]
        lessons: list[str] = []
        for run in reversed(runs):
            for lesson in reversed(run.get("lessons", [])):
                lesson_text = str(lesson or "").strip()
                if lesson_text and lesson_text not in lessons:
                    lessons.append(lesson_text)
                if len(lessons) >= limit:
                    return list(reversed(lessons))
        return list(reversed(lessons))

    @staticmethod
    def _latest_simulation_results(runs: list[dict[str, object]]) -> list[dict[str, object]]:
        latest_by_name: dict[str, dict[str, object]] = {}
        for run in runs:
            latest_by_name[str(run.get("name", "unknown"))] = run
        return list(latest_by_name.values())

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

    def _research_api_key(self) -> str:
        secrets = self._load_streamlit_secrets()
        candidates = [
            os.getenv("MANTIS_RESEARCH_API_KEY"),
            os.getenv("TAVILY_API_KEY"),
            secrets.get("MANTIS_RESEARCH_API_KEY"),
            secrets.get("TAVILY_API_KEY"),
            secrets.get("tavily_api_key"),
            self._nested_secret(secrets, "research", "api_key"),
            self._nested_secret(secrets, "tavily", "api_key"),
        ]
        for key in candidates:
            clean = str(key or "").strip()
            if clean:
                return clean
        return ""

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

    @staticmethod
    def _slugify(value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return slug or "item"

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
        text = str(value)
        patterns = [
            (r"\bgsk_[A-Za-z0-9_-]{8,}\b", "gsk_***MASKED***"),
            (r"\bre_[A-Za-z0-9_-]{12,}\b", "re_***MASKED***"),
            (r"\bGOCSPX-[A-Za-z0-9_-]{8,}\b", "GOCSPX-***MASKED***"),
            (r"\b[0-9]{6,}-[A-Za-z0-9_-]{20,}\.apps\.googleusercontent\.com\b", "***GOOGLE_CLIENT_ID***"),
            (r"\bsk-[A-Za-z0-9_-]{12,}\b", "sk-***MASKED***"),
        ]
        for pattern, replacement in patterns:
            text = re.sub(pattern, replacement, text)
        return text

    @classmethod
    def _contains_secret(cls, value: str) -> bool:
        return cls._mask_secrets(value) != str(value)

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
        return "\033[92m  MANTIS \033[96m>\033[0m "

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

    def _extract_todo_request(self, text: str) -> str | None:
        clean = re.sub(r"\s+", " ", text or "").strip()
        lowered = clean.lower()
        if not re.search(r"\b(todo|to-do|task list|list)\b", lowered):
            return None
        add_match = re.search(r"\b(?:add|save|put)\s+(.+?)\s+(?:to|in|into|on)\s+(?:the\s+)?(?:todo|to-do|task list|list)\b", clean, re.I)
        if add_match:
            return add_match.group(1).strip()
        if re.search(r"\b(make|create|save|write)\s+(that|the)\s+(?:(?:todo|to-do|task)\s+)?list\b.*$", lowered):
            return "that list"
        if re.search(r"\b(add|save)\s+(that|the)\s+(?:to|in|into|on)\s+(?:the\s+)?(?:todo|to-do|task list|list)\b.*$", lowered):
            return "that list"
        return None

    @staticmethod
    def _extract_auto_lesson(text: str) -> str:
        clean = re.sub(r"\s+", " ", text or "").strip()
        lowered = clean.lower()
        if not clean or len(clean) < 12:
            return ""
        patterns = [
            r"\bi need you to understand\s+(.+)$",
            r"\bremember this[:\s]+(.+)$",
            r"\banother thing to fix[:\s]+(.+)$",
            r"\bfix this[:\s]+(.+)$",
            r"\bplease learn\s+(.+)$",
        ]
        for pattern in patterns:
            match = re.search(pattern, clean, re.I)
            if match:
                return "User behavior guidance: " + match.group(1).strip()
        if re.search(r"\b(you|u|mantis)\b.*\b(not listening|did it again|not hearing|missing what i mean)\b", lowered):
            return "When the user says MANTIS is not listening, slow down, reflect the exact point, and avoid repeating the previous mistake."
        if re.search(r"\bif\s+i\s+say\b.+\bdoesn'?t\s+mean\b", lowered):
            return "Do not treat casual mentions as commands; wait for an explicit slash command before showing status, logs, simulator results, or restarting."
        if re.search(r"\b(don't|dont|do not)\s+(mention|say|call|assume|repeat|show)\b", lowered):
            return "Respect direct user preference: " + clean
        if re.search(r"\bslash command\b", lowered) and re.search(r"\b(status|logs|simulator|restart|command)\b", lowered):
            return "Launcher actions should require slash commands; normal text should stay conversational."
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
    parser.add_argument("--memory-file", default="")
    parser.add_argument("--drills-file", default="")
    parser.add_argument("--handoff", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    return LauncherChat(args).run()


if __name__ == "__main__":
    raise SystemExit(main())
