from unittest import mock

from django.test import TestCase

from trainer.services import EtudeGenerationError, EtudeService


class EtudeServiceTests(TestCase):
    def _service(self, abc):
        repo = mock.Mock(get_latest_abc=mock.Mock(return_value=abc))
        return EtudeService(repository=repo)

    @mock.patch("trainer.services.etude_service.subprocess.run")
    def test_generate_returns_abc(self, run):
        run.return_value = mock.Mock(returncode=0, stderr="")
        self.assertEqual(self._service("X:1").generate(), "X:1")

    @mock.patch("trainer.services.etude_service.subprocess.run")
    def test_generate_raises_on_script_failure(self, run):
        run.return_value = mock.Mock(returncode=1, stderr="boom")
        with self.assertRaisesMessage(EtudeGenerationError, "boom"):
            self._service("X:1").generate()
