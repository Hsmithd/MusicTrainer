from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase


class PageTests(TestCase):
    def test_pages_render(self):
        for url in ("/", "/home", "/profile", "/login", "/signup"):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_login_redirects_on_success(self):
        User.objects.create_user("alice", password="pw-12345")
        resp = self.client.post("/login", {"username": "alice", "password": "pw-12345"})
        self.assertRedirects(resp, "/home", fetch_redirect_response=False)


class GenerateEtudeViewTests(TestCase):
    @mock.patch("trainer.services.etude_service.subprocess.run")
    def test_returns_error_json(self, run):
        run.return_value = mock.Mock(returncode=1, stderr="boom")
        resp = self.client.post("/api/generate-etude/")
        self.assertEqual(resp.json(), {"success": False, "error": "boom"})
