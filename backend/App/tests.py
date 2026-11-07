import os
import tempfile
from pathlib import Path
from unittest import mock

from django.test import TestCase

from App.repositories import EtudeRepository, UserRepository
from App.services import EtudeGenerationError, EtudeService


class EtudeRepositoryTests(TestCase):
    def test_returns_none_when_no_files(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(EtudeRepository(d).get_latest_abc())

    def test_returns_latest_file(self):
        with tempfile.TemporaryDirectory() as d:
            old, new = Path(d, "a.abc"), Path(d, "b.abc")
            old.write_text("old")
            new.write_text("new")
            os.utime(old, (1, 1))
            self.assertEqual(EtudeRepository(d).get_latest_abc(), "new")


class UserRepositoryTests(TestCase):
    def test_username_exists(self):
        from django.contrib.auth.models import User
        User.objects.create_user("alice", password="x")
        repo = UserRepository()
        self.assertTrue(repo.username_exists("alice"))
        self.assertIsNone(repo.get_by_username("bob"))


class EtudeServiceTests(TestCase):
    def _service(self, abc):
        repo = mock.Mock(get_latest_abc=mock.Mock(return_value=abc))
        return EtudeService(repository=repo)

    @mock.patch("App.services.etude_service.subprocess.run")
    def test_generate_returns_abc(self, run):
        run.return_value = mock.Mock(returncode=0, stderr="")
        self.assertEqual(self._service("X:1").generate(), "X:1")

    @mock.patch("App.services.etude_service.subprocess.run")
    def test_generate_raises_on_script_failure(self, run):
        run.return_value = mock.Mock(returncode=1, stderr="boom")
        with self.assertRaisesMessage(EtudeGenerationError, "boom"):
            self._service("X:1").generate()

    @mock.patch("App.services.etude_service.subprocess.run")
    def test_generate_view(self, run):
        run.return_value = mock.Mock(returncode=1, stderr="boom")
        resp = self.client.post("/api/generate-etude/")
        self.assertEqual(resp.json(), {"success": False, "error": "boom"})
