"""Integration smoke tests for the Seoul local web API (no external API keys)."""
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

import seoul_web
from core.config_manager import ConfigManager


class SeoulWebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = seoul_web.ThreadingHTTPServer(("127.0.0.1", 0), seoul_web.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = "http://127.0.0.1:" + str(cls.server.server_address[1])

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)

    def call(self, path, payload=None, token=True):
        headers = {"Host": "127.0.0.1", "Content-Type": "application/json"}
        if token:
            headers["X-Seoul-Token"] = seoul_web.TOKEN
        req = urllib.request.Request(
            self.base + path,
            data=None if payload is None else json.dumps(payload).encode(),
            headers=headers,
            method="GET" if payload is None else "POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status, r.read().decode()
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode()

    def test_windows_bom_settings_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "settings.json"
            path.write_bytes(b"\\xef\\xbb\\xbf" + b'{"default_prefix":"seoul_"}')
            self.assertEqual(ConfigManager().load_json(path)["default_prefix"], "seoul_")

    def test_home_serves_ui(self):
        code, html = self.call("/")
        self.assertEqual(code, 200)
        self.assertIn("seoul", html.lower())
        self.assertIn("IA Local", html)

    def test_authentication_required(self):
        code, _ = self.call("/api/settings", token=False)
        self.assertEqual(code, 403)

    def test_settings_read(self):
        code, body = self.call("/api/settings")
        self.assertEqual(code, 200)
        self.assertIn("ollama", json.loads(body)["providers"])

    def test_chat_ollama_mocked(self):
        with patch.object(seoul_web, "prefs", return_value={"mode": "local", "provider": "ollama", "model": "test", "fallbacks": []}), patch.object(seoul_web, "chat", return_value="resposta real simulada"):
            code, body = self.call("/api/chat", {"message": "Olá", "history": []})
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(body)["answer"], "resposta real simulada")

    def test_auto_fallback_mocked(self):
        def fake_chat(provider, model, messages):
            if provider == "ollama":
                raise RuntimeError("offline")
            return "fallback OK"
        config = {"mode": "auto", "provider": "ollama", "model": "test", "fallbacks": [{"provider": "gemini", "model": "test-model"}]}
        with patch.object(seoul_web, "prefs", return_value=config), patch.object(seoul_web, "chat", side_effect=fake_chat):
            code, body = self.call("/api/chat", {"message": "Teste", "history": []})
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(body)["provider"], "gemini")
        self.assertEqual(len(json.loads(body)["attempts"]), 1)

    def test_ollama_cloud_uses_ollama_endpoint(self):
        with patch.object(seoul_web, "request_json", return_value={"message": {"content": "resposta cloud"}}) as request:
            result = seoul_web.chat("ollama_cloud", "glm-5:cloud", [{"role": "user", "content": "oi"}])
        self.assertEqual(result, "resposta cloud")
        self.assertEqual(request.call_args.args[0], "http://127.0.0.1:11434/api/chat")

    def test_ollama_cloud_rejects_local_model(self):
        with self.assertRaises(ValueError):
            seoul_web.chat("ollama_cloud", "qwen2.5-coder:7b", [{"role": "user", "content": "oi"}])

    def test_cloud_mode_preserves_existing_chat_flow(self):
        config = {"mode": "cloud", "provider": "ollama_cloud", "model": "glm-5:cloud", "fallbacks": []}
        with patch.object(seoul_web, "prefs", return_value=config), patch.object(seoul_web, "chat", return_value="nuvem ok"):
            code, body = self.call("/api/chat", {"message": "Teste", "history": []})
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(body)["provider"], "ollama_cloud")

    def test_ollama_installed_does_not_download(self):
        with patch.object(seoul_web, "ollama_model_installed", return_value=True), patch.object(seoul_web.threading, "Thread") as thread:
            code, body = self.call("/api/ollama/install", {})
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(body)["status"], "ready")
        thread.assert_not_called()

    def test_ollama_missing_starts_download(self):
        with patch.object(seoul_web, "ollama_model_installed", return_value=False), patch.object(seoul_web.threading, "Thread") as thread:
            code, body = self.call("/api/ollama/install", {})
        self.assertEqual(code, 202)
        self.assertEqual(json.loads(body)["status"], "downloading")
        thread.assert_called_once()
        with seoul_web.PULL_LOCK:
            seoul_web.PULL_STATE["status"] = "idle"

    def test_ollama_unavailable_reports_error(self):
        with patch.object(seoul_web, "ollama_model_installed", return_value=None):
            code, body = self.call("/api/ollama/install", {})
        self.assertEqual(code, 503)
        self.assertEqual(json.loads(body)["status"], "unavailable")

    def test_detector_unknown_folder(self):
        code, body = self.call("/api/detect", {"path": "/a/path/that/does/not/exist"})
        self.assertEqual(code, 400)

    def test_detector_qbox(self):
        with tempfile.TemporaryDirectory() as tmp:
            resource = Path(tmp) / "resources" / "qbx_core"
            resource.mkdir(parents=True)
            (resource / "fxmanifest.lua").write_text("fx_version 'cerulean'", encoding="utf-8")
            code, body = self.call("/api/detect", {"path": tmp})
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(body)["primary_framework"], "qbox")


if __name__ == "__main__":
    unittest.main()
