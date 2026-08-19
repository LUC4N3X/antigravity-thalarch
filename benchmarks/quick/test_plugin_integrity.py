#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import plugin_integrity as integrity


class PluginIntegrityTests(unittest.TestCase):
    def _write_tree(self, root: Path, suffix: str = "") -> None:
        (root / "skills" / "thalarch-mode").mkdir(parents=True, exist_ok=True)
        (root / "agents" / "thalarch-orchestrator").mkdir(parents=True, exist_ok=True)
        (root / "hooks").mkdir(parents=True, exist_ok=True)
        (root / "plugin.json").write_text('{"name":"thalarch-mode"}\n', encoding="utf-8")
        (root / "hooks.json").write_text('{"hooks":[]}\n', encoding="utf-8")
        (root / "skills" / "thalarch-mode" / "SKILL.md").write_text(f"skill{suffix}\n", encoding="utf-8")
        (root / "agents" / "thalarch-orchestrator" / "agent.md").write_text("agent\n", encoding="utf-8")
        (root / "hooks" / "gate.py").write_text("print('gate')\n", encoding="utf-8")

    def test_explicit_exact_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "source"
            staged = base / "staged"
            self._write_tree(source)
            self._write_tree(staged)
            result = integrity.verify_plugin_tree(staged_root=staged, source_root=source)
            self.assertTrue(result["match"])
            self.assertEqual(result["source_fingerprint"], result["staged_fingerprint"])

    def test_explicit_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "source"
            staged = base / "staged"
            self._write_tree(source)
            self._write_tree(staged, suffix="-changed")
            result = integrity.verify_plugin_tree(staged_root=staged, source_root=source)
            self.assertFalse(result["match"])
            self.assertIn("skills/thalarch-mode/SKILL.md", result["mismatched"])

    def test_non_behavior_metadata_does_not_break_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "source"
            staged = base / "staged"
            self._write_tree(source)
            self._write_tree(staged)
            (staged / "install-metadata.lock").write_text("ignored\n", encoding="utf-8")
            result = integrity.verify_plugin_tree(staged_root=staged, source_root=source)
            self.assertTrue(result["match"])

    def test_missing_staged_tree_reports_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "source"
            missing = base / "missing"
            self._write_tree(source)
            result = integrity.verify_plugin_tree(staged_root=missing, source_root=source)
            self.assertFalse(result["match"])
            self.assertEqual(result["candidate_count"], 1)
            self.assertEqual(result["candidate_roots"], [str(missing)])


if __name__ == "__main__":
    unittest.main()
