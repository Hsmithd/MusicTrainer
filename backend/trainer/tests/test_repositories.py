import tempfile
from pathlib import Path

from django.contrib.auth.models import User
from django.test import TestCase

from trainer.repositories import EtudeRepository, UserRepository


class EtudeRepositoryTests(TestCase):
    def test_new_output_paths_are_unique_and_in_output_dir(self):
        with tempfile.TemporaryDirectory() as d:
            repo = EtudeRepository(Path(d, "out"))
            a, b = repo.new_output_path(), repo.new_output_path()
            self.assertNotEqual(a, b)
            self.assertEqual(a.parent, Path(d, "out"))
            self.assertTrue(a.parent.is_dir())

    def test_read(self):
        with tempfile.TemporaryDirectory() as d:
            repo = EtudeRepository(d)
            path = repo.new_output_path()
            self.assertIsNone(repo.read(path))
            path.write_text("X:1")
            self.assertEqual(repo.read(path), "X:1")


class UserRepositoryTests(TestCase):
    def test_username_exists(self):
        User.objects.create_user("alice", password="x")
        repo = UserRepository()
        self.assertTrue(repo.username_exists("alice"))
        self.assertIsNone(repo.get_by_username("bob"))
