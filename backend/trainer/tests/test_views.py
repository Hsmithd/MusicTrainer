import tempfile
from pathlib import Path
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase, override_settings


class ReactPageTests(TestCase):
    def setUp(self):
        self.build_dir = tempfile.TemporaryDirectory()
        Path(self.build_dir.name, "index.html").write_text("<div id='root'></div>")
        self.settings_override = override_settings(FRONTEND_BUILD_DIR=Path(self.build_dir.name))
        self.settings_override.enable()

    def tearDown(self):
        self.settings_override.disable()
        self.build_dir.cleanup()

    def test_react_routes_serve_index(self):
        for url in ("/", "/home", "/profile", "/some/new/page"):
            with self.subTest(url=url):
                resp = self.client.get(url)
                self.assertEqual(resp.status_code, 200)
                self.assertContains(resp, "id='root'")

    def test_api_and_admin_are_not_caught(self):
        self.assertEqual(self.client.get("/api/unknown/").status_code, 404)
        self.assertNotContains(self.client.get("/admin/", follow=True), "id='root'")

    def test_missing_build_explains_what_to_do(self):
        with override_settings(FRONTEND_BUILD_DIR=Path(self.build_dir.name, "missing")):
            resp = self.client.get("/home")
        self.assertEqual(resp.status_code, 503)
        self.assertContains(resp, "npm run build", status_code=503)


class AuthPageTests(TestCase):
    def test_pages_render(self):
        for url in ("/login", "/signup"):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_login_redirects_on_success(self):
        User.objects.create_user("alice", password="pw-12345")
        resp = self.client.post("/login", {"username": "alice", "password": "pw-12345"})
        self.assertRedirects(resp, "/home", fetch_redirect_response=False)


class GenerateEtudeViewTests(TestCase):
    def post(self, body):
        return self.client.post("/api/generate-etude/", body, content_type="application/json")

    @mock.patch("trainer.views.EtudeService.generate", return_value="X:1")
    def test_passes_difficulty_to_service(self, generate):
        resp = self.post({"difficulty": "easy"})
        self.assertEqual(resp.json()["abc_notation"], "X:1")
        generate.assert_called_once_with("easy")

    @mock.patch("trainer.views.EtudeService.generate", return_value="X:1")
    def test_difficulty_is_optional(self, generate):
        self.post({})
        generate.assert_called_once_with(None)

    def test_rejects_bad_requests(self):
        self.assertEqual(self.post({"difficulty": "extreme"}).status_code, 400)
        self.assertEqual(self.post("not json").status_code, 400)
        self.assertEqual(self.post([1, 2]).status_code, 400)

    @mock.patch("trainer.services.etude_service.subprocess.run")
    def test_returns_error_json(self, run):
        run.return_value = mock.Mock(returncode=1, stderr="boom")
        resp = self.post({"difficulty": "medium"})
        self.assertEqual(resp.json(), {"success": False, "error": "boom"})
