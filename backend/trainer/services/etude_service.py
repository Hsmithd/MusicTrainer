import subprocess

from django.conf import settings

from trainer.repositories import EtudeRepository


class EtudeGenerationError(Exception):
    pass


class EtudeService:
    """Generates practice etudes by running the MelodyT5 inference script."""

    DIFFICULTIES = ("easy", "medium", "hard")

    INFERENCE_ARGS = [
        "-num_tunes", "1",
        "-max_patch", "128",
        "-top_p", "0.8",
        "-top_k", "8",
        "-temperature", "2.6",
        "-show_control_code", "True",
    ]

    def __init__(self, repository=None):
        self.repository = repository or EtudeRepository()

    def generate(self, difficulty=None):
        """Run the model and return the generated ABC notation.

        ``difficulty`` is "easy", "medium" or "hard". It only has an effect
        once the difficulty fine-tuned weights exist (see ml/melodyt5/config.py).
        """
        if difficulty is not None and difficulty not in self.DIFFICULTIES:
            raise ValueError(f"difficulty must be one of {', '.join(self.DIFFICULTIES)}")

        model_dir = settings.MELODYT5_DIR
        output_path = self.repository.new_output_path()
        command = [settings.MELODYT5_PYTHON, str(model_dir / "inference.py"),
                   *self.INFERENCE_ARGS, "-output", str(output_path)]
        if difficulty:
            command += ["-difficulty", difficulty]

        result = subprocess.run(command, capture_output=True, text=True, cwd=model_dir)
        if result.returncode != 0:
            raise EtudeGenerationError(result.stderr or "Script execution failed")

        abc = self.repository.read(output_path)
        if abc is None:
            raise EtudeGenerationError("No output file generated")
        return abc
