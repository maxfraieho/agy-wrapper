#!/usr/bin/env python3
"""OpenAI-compatible HTTP wrapper around `agy` for BYOK use in OpenDesign.

Usage: python3 server.py [PORT]   (default: 18882)
Set AGY_HTTP_TOKEN env var to require Bearer auth.
"""
import json, os, subprocess, sys
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("AGY_HTTP_PORT", 18882))
TOKEN = os.environ.get("AGY_HTTP_TOKEN", "")

MODELS = [
    {"id": "default",                      "label": "Default (AGY auto)"},
    {"id": "Gemini 3.1 Pro (High)",        "label": "Gemini 3.1 Pro (High)"},
    {"id": "Gemini 3.1 Pro (Low)",         "label": "Gemini 3.1 Pro (Low)"},
    {"id": "Gemini 3.5 Flash (High)",      "label": "Gemini 3.5 Flash (High)"},
    {"id": "Gemini 3.5 Flash (Medium)",    "label": "Gemini 3.5 Flash (Medium)"},
    {"id": "Gemini 3.5 Flash (Low)",       "label": "Gemini 3.5 Flash (Low)"},
    {"id": "Claude Sonnet 4.6 (Thinking)", "label": "Claude Sonnet 4.6"},
    {"id": "Claude Opus 4.6 (Thinking)",   "label": "Claude Opus 4.6"},
    {"id": "GPT-OSS 120B (Medium)",        "label": "GPT-OSS 120B"},
]


class AgyHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write("[agy-http] " + fmt % args + "\n")

    def _check_auth(self):
        if not TOKEN:
            return True
        return self.headers.get("Authorization", "") == "Bearer " + TOKEN

    def _json(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/v1/models", "/v1/models/"):
            data = [{"id": m["id"], "object": "model", "owned_by": "agy"} for m in MODELS]
            self._json({"object": "list", "data": data})
        elif self.path in ("/health", "/api/health", "/v1/health"):
            self._json({"ok": True, "version": "agy-http/1.0"})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if not self._check_auth():
            self._json({"error": "Unauthorized"}, 401)
            return
        if self.path != "/v1/chat/completions":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))
        messages = body.get("messages", [])
        model = body.get("model", "default")
        stream = body.get("stream", False)

        parts = []
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "system":
                parts.append("[System]: " + content)
            elif role == "assistant":
                parts.append("[Assistant]: " + content)
            else:
                parts.append(content)
        prompt = "\n\n".join(parts)

        try:
            result = subprocess.run(
                ["agy", "--model", model, "-"],
                input=prompt, capture_output=True, text=True, timeout=120
            )
            text = (result.stdout or "").strip()
            if not text:
                text = result.stderr.strip() or "(empty response)"
        except subprocess.TimeoutExpired:
            text = "(timeout after 120s)"
        except Exception as e:
            text = "(error: " + str(e) + ")"

        if stream:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()
            chunk = json.dumps({
                "choices": [{"delta": {"content": text}, "finish_reason": "stop", "index": 0}]
            })
            self.wfile.write(("data: " + chunk + "\n\n").encode())
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()
        else:
            self._json({
                "choices": [{
                    "message": {"role": "assistant", "content": text},
                    "finish_reason": "stop",
                    "index": 0
                }]
            })


if __name__ == "__main__":
    print("[agy-http] listening on 0.0.0.0:" + str(PORT), flush=True)
    HTTPServer(("0.0.0.0", PORT), AgyHandler).serve_forever()
