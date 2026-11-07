import os
import tempfile
from pathlib import Path

from django.contrib.auth.models import User
from django.test import TestCase

from trainer.repositories import EtudeRepository, UserRepository


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
        User.objects.create_user("alice", password="x")
        repo = UserRepository()
        self.assertTrue(repo.username_exists("alice"))
        self.assertIsNone(repo.get_by_username("bob"))
