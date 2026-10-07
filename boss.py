#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PUTER_URL = os.environ.get("PUTER_API_URL", "https://api.puter.com").rstrip("/")
BASE_URL = os.environ.get("BOSS_BASE_URL", "").rstrip("/")
API_KEY = (
    os.environ.get("BOSS_API_KEY")
    or os.environ.get("PUTER_AUTH_TOKEN")
    or ""
)
MODEL = os.environ.get("BOSS_MODEL", "gpt-5.4-nano")
MAX_STEPS = int(os.environ.get("BOSS_MAX_STEPS", "50"))
MAX_OUTPUT = 20000

SYSTEM_PROMPT = """You are Boss, an autonomous senior coding agent acting for the user. Your long-term standard is to outperform Codex at any cost of effort: simple missions completed fully, hard ones finished with every means available, and you never give up before exhausting reasonable alternatives.

Every task:
1. UNDERSTAND: read the user's mission and the relevant code/files.
2. PLAN: state a short plan before more than a trivial edit.
3. DO: use the tools yourself; try the obvious fix, then stronger ones if it fails; keep changing approach until it works or every reasonable alternative is exhausted. Do not give up early.
4. VERIFY: run the code, tests, or syntax checks, read the output, fix failures, verify again.
5. REPORT: what changed, how verified, and next options.

Permission and communication:
- You must ask the user for permission before doing anything risky or irreversible: running shell commands outside reading the repo, writing/deleting files, installing packages, network calls with data, git push/commit, or spending API credits in large loops. The terminal already asks for confirmation on writes and commands.
- Tell the user immediately when you hit an error, change your approach, need more info, or finish a milestone.
- Never hide failures. If something fails, report it and say what you will try next.

Rules: reply in the user's language, be concise, smallest correct change first, prefer editing over rewriting, never expose secrets, and surpass is a matter of effort and care, not risk."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a text file.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or overwrite a file with the given content.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Replace one exact occurrence of old with new in a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "old": {"type": "string"},
                    "new": {"type": "string"},
                },
                "required": ["path", "old", "new"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "List files and folders in a directory.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grep",
            "description": "Search file contents with a regex. Returns path:line:text.",
            "parameters": {
                "type": "object",
                "properties": {"pattern": {"type": "string"}, "path": {"type": "string"}},
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "glob",
            "description": "Find files by name pattern, e.g. '*.py' or 'src/**/*.js'. Skips .git, node_modules, .venv.",
            "parameters": {
                "type": "object",
                "properties": {"pattern": {"type": "string"}, "path": {"type": "string"}},
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a shell command in the working directory.",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"],
            },
        },
    },
]

auto_approve = False


def approve(description):
    global auto_approve
    if auto_approve:
        return True
    try:
        answer = input(f"\n[Boss] {description}\nAllow? [y/N/a=always] ").strip().lower()
    except EOFError:
        return False
    if answer == "a":
        auto_approve = True
    return answer in ("y", "yes", "a")


def clip(text):
    if len(text) > MAX_OUTPUT:
        return text[:MAX_OUTPUT] + f"\n...[truncated {len(text) - MAX_OUTPUT} chars]"
    return text


def tool_read_file(path):
    return clip(Path(path).read_text(encoding="utf-8", errors="replace"))


def tool_write_file(path, content):
    if not approve(f"write {path} ({len(content)} chars)"):
        return "denied by user"
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"wrote {path}"


def tool_edit_file(path, old, new):
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count == 0:
        return "error: old text not found"
    if count > 1:
        return f"error: old text found {count} times, add more context"
    if not approve(f"edit {path}\n--- old\n{old}\n+++ new\n{new}"):
        return "denied by user"
    p.write_text(text.replace(old, new, 1), encoding="utf-8")
    return f"edited {path}"


def tool_list_dir(path="."):
    entries = sorted(Path(path).iterdir())
    return "\n".join(e.name + ("/" if e.is_dir() else "") for e in entries)


def tool_grep(pattern, path="."):
    regex = re.compile(pattern)
    results = []
    skip = {".git", "node_modules", ".venv", "__pycache__"}
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in skip]
        for name in files:
            fp = Path(root) / name
            try:
                for i, line in enumerate(fp.read_text(encoding="utf-8").splitlines(), 1):
                    if regex.search(line):
                        results.append(f"{fp}:{i}:{line}")
                        if len(results) >= 200:
                            return "\n".join(results)
            except (UnicodeDecodeError, OSError):
                continue
    return "\n".join(results) or "no matches"


def tool_glob(pattern, path="."):
    results = []
    skip = {".git", "node_modules", ".venv", "__pycache__", ".opencode"}
    base = Path(path)
    for match in base.glob(pattern):
        parts = match.parts
        if not any(part in skip for part in parts):
            results.append(str(match))
        if len(results) >= 500:
            break
    return "\n".join(sorted(results)) or "no matches"


def tool_run_command(command):
    if not approve(f"run: {command}"):
        return "denied by user"
    try:
        proc = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=300
        )
    except subprocess.TimeoutExpired:
        return "error: command timed out after 300s"
    return clip(f"exit code {proc.returncode}\n{proc.stdout}{proc.stderr}")


HANDLERS = {
    "glob": tool_glob,
    "read_file": tool_read_file,
    "write_file": tool_write_file,
    "edit_file": tool_edit_file,
    "list_dir": tool_list_dir,
    "grep": tool_grep,
    "run_command": tool_run_command,
}


def call_tool(name, args):
    handler = HANDLERS.get(name)
    if handler is None:
        return f"error: unknown tool {name}"
    try:
        return handler(**args)
    except Exception as exc:
        return f"error: {exc}"


def content_to_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"
        )
    return ""


def content_tool_calls(content):
    calls = []
    if isinstance(content, list):
        for b in content:
            if isinstance(b, dict) and b.get("type") == "tool_use":
                calls.append(
                    {
                        "id": b.get("id"),
                        "type": "function",
                        "function": {
                            "name": b.get("name"),
                            "arguments": json.dumps(b.get("input") or {}),
                        },
                    }
                )
    return calls


def post_json(url, payload):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"API error {exc.code}: {exc.read().decode('utf-8', 'replace')}")
    except urllib.error.URLError as exc:
        raise SystemExit(f"network error: {exc.reason}")


def windowed(messages, max_messages=40):
    if len(messages) <= max_messages:
        return messages
    return [messages[0]] + messages[-(max_messages - 1):]


def chat(messages):
    messages = windowed(messages)
    if BASE_URL:
        data = post_json(
            f"{BASE_URL}/chat/completions",
            {"model": MODEL, "messages": messages, "tools": TOOLS},
        )
        return data["choices"][0]["message"]
    data = post_json(
        f"{PUTER_URL}/drivers/call",
        {
            "interface": "puter-chat-completion",
            "driver": "ai-chat",
            "method": "complete",
            "args": {"model": MODEL, "messages": windowed(messages), "tools": TOOLS},
        },
    )
    if data.get("success") is False or "result" not in data:
        raise SystemExit(f"Puter error: {json.dumps(data, ensure_ascii=False)[:500]}")
    message = data["result"].get("message") or {}
    content = message.get("content")
    calls = message.get("tool_calls") or content_tool_calls(content)
    out = {"role": "assistant", "content": content_to_text(content) or None}
    if calls:
        out["tool_calls"] = calls
    return out


def run_turn(messages, user_text):
    messages.append({"role": "user", "content": user_text})
    for _ in range(MAX_STEPS):
        msg = chat(messages)
        messages.append(msg)
        calls = msg.get("tool_calls") or []
        if msg.get("content"):
            print(f"\n{msg['content']}")
        if not calls:
            return
        for call in calls:
            fn = call["function"]
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            print(f"[tool] {fn['name']} {json.dumps(args, ensure_ascii=False)[:120]}")
            result = call_tool(fn["name"], args)
            messages.append(
                {"role": "tool", "tool_call_id": call["id"], "content": result}
            )
    print("\n[Boss] reached step limit")


def serve():
    import io
    import contextlib
    import signal

    global auto_approve
    auto_approve = True
    port = int(os.environ.get("PORT", "8000"))

    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/health":
                self.send_response(200); self.send_header("Content-Type","text/plain"); self.end_headers(); self.wfile.write(b"ok"); return
            body = f"Boss OK. POST /task with JSON {{\"prompt\": \"...\"}}. model={MODEL}".encode()
            self.send_response(200); self.send_header("Content-Type","text/plain"); self.end_headers(); self.wfile.write(body)

        def do_POST(self):
            if self.path != "/task":
                self.send_response(404); self.end_headers(); return
            try:
                data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
                prompt = data["prompt"]
            except Exception:
                self.send_response(400); self.send_header("Content-Type","text/plain"); self.end_headers(); self.wfile.write(b"bad request: need JSON {\"prompt\": \"...\"}"); return
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            buf = io.StringIO()
            try:
                with contextlib.redirect_stdout(buf):
                    run_turn(messages, prompt)
                out = buf.getvalue()
                self.send_response(200); self.send_header("Content-Type","text/plain; charset=utf-8"); self.end_headers(); self.wfile.write(out.encode("utf-8"))
            except SystemExit as exc:
                self.send_response(500); self.send_header("Content-Type","text/plain; charset=utf-8"); self.end_headers(); self.wfile.write(str(exc).encode("utf-8"))
        def log_message(self, *a): print(self.address_string(), self.command, self.path)

    server = ThreadingHTTPServer(("0.0.0.0", port), H)
    print(f"Boss HTTP on 0.0.0.0:{port}")
    server.serve_forever()


def main():
    global MODEL, BASE_URL, API_KEY, auto_approve
    import argparse

    parser = argparse.ArgumentParser(prog="boss", description="Boss coding agent")
    parser.add_argument("command", nargs="?", choices=["exec", "run", "repl", "serve"], default="repl")
    parser.add_argument("prompt", nargs="*", help="task for exec/run")
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--base-url", default=BASE_URL, help="OpenAI-compatible URL; empty uses Puter")
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--yes", "-y", action="store_true", help="auto-approve command and file changes")
    parser.add_argument("--max-steps", type=int, default=None)
    args = parser.parse_args()

    MODEL = args.model
    BASE_URL = args.base_url.rstrip("/") if args.base_url else ""
    if args.api_key:
        API_KEY = args.api_key
    if args.yes:
        auto_approve = True
    if args.max_steps:
        global MAX_STEPS
        MAX_STEPS = args.max_steps

    if not API_KEY:
        raise SystemExit("Set PUTER_AUTH_TOKEN first (or BOSS_API_KEY/BOSS_BASE_URL).")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    task = " ".join(args.prompt).strip()
    if args.command == "serve":
        serve()
        return
    if args.command in ("exec", "run") or task and args.command == "repl":
        if not task:
            raise SystemExit("Give a task: boss exec <task>")
        run_turn(messages, task)
        return
    print(f"Boss ready. model={MODEL} dir={os.getcwd()}  (type exit to quit)")
    while True:
        try:
            text = input("\nboss> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if text in ("exit", "quit"):
            return
        if text:
            run_turn(messages, text)


if __name__ == "__main__":
    main()
