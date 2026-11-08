from pathlib import Path
from unittest import mock

from django.test import TestCase

from trainer.services import EtudeGenerationError, EtudeService


class EtudeServiceTests(TestCase):
    def setUp(self):
        self.repo = mock.Mock(new_output_path=mock.Mock(return_value=Path("/tmp/etude_x.abc")),
                              read=mock.Mock(return_value="X:1"))
        self.service = EtudeService(repository=self.repo)

    @mock.patch("trainer.services.etude_service.subprocess.run")
    def test_generate_returns_abc_from_its_own_output_file(self, run):
        run.return_value = mock.Mock(returncode=0, stderr="")
        self.assertEqual(self.service.generate(), "X:1")
        command = run.call_args.args[0]
        self.assertEqual(command[command.index("-output") + 1], str(Path("/tmp/etude_x.abc")))
        self.assertNotIn("-difficulty", command)
        self.repo.read.assert_called_once_with(Path("/tmp/etude_x.abc"))

    @mock.patch("trainer.services.etude_service.subprocess.run")
    def test_generate_passes_difficulty(self, run):
        run.return_value = mock.Mock(returncode=0, stderr="")
        self.service.generate("hard")
        command = run.call_args.args[0]
        self.assertEqual(command[command.index("-difficulty") + 1], "hard")

    def test_rejects_unknown_difficulty(self):
        with self.assertRaises(ValueError):
            self.service.generate("extreme")

    @mock.patch("trainer.services.etude_service.subprocess.run")
    def test_generate_raises_on_script_failure(self, run):
        run.return_value = mock.Mock(returncode=1, stderr="boom")
        with self.assertRaisesMessage(EtudeGenerationError, "boom"):
            self.service.generate()

    @mock.patch("trainer.services.etude_service.subprocess.run")
    def test_generate_raises_when_no_output(self, run):
        run.return_value = mock.Mock(returncode=0, stderr="")
        self.repo.read.return_value = None
        with self.assertRaisesMessage(EtudeGenerationError, "No output file generated"):
            self.service.generate()
