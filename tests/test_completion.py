"""Unit tests for Shell Autocompletion script generation."""

import unittest
from resume_forge.completion import generate_bash_completion, generate_zsh_completion, generate_fish_completion


class TestCompletion(unittest.TestCase):

    def test_bash_completion(self):
        bash = generate_bash_completion()
        self.assertIn("_resume_forge_completion()", bash)
        self.assertIn("cern harvard jakes minimalist quant awesome academic", bash)
        self.assertIn("compile export audit diff letter", bash)
        self.assertIn("complete -F _resume_forge_completion resume-forge", bash)

    def test_zsh_completion(self):
        zsh = generate_zsh_completion()
        self.assertIn("#compdef resume-forge", zsh)
        self.assertIn("_arguments", zsh)
        self.assertIn("compile", zsh)
        self.assertIn("letter", zsh)
        self.assertIn("diff", zsh)
        self.assertIn("harvard", zsh)

    def test_fish_completion(self):
        fish = generate_fish_completion()
        self.assertIn("complete -c resume-forge", fish)
        self.assertIn("harvard", fish)
        self.assertIn("diff", fish)


if __name__ == "__main__":
    unittest.main()
