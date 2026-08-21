from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmarks"))
sys.path.insert(0, str(ROOT / "benchmarks" / "ablation"))
sys.path.insert(0, str(ROOT / "benchmarks" / "holdout"))
sys.path.insert(0, str(ROOT / "benchmarks" / "hosts"))
sys.path.insert(0, str(ROOT / "benchmarks" / "long"))

import publish_run
import verify_published_run
import run_ablation
import run_holdout
import run_longbench
from host_command import render_command


class PublicationTests(unittest.TestCase):
    def test_public_manifest_is_sanitized_and_self_verifying(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp)
            (run / "results").mkdir()
            manifest = {
                "run_id": "unit",
                "requested_model": "model-x",
                "effort": "high",
                "protocol_revision": 4,
                "protocol_fingerprint": "abc",
                "benchmark_revision": "def",
                "agy_version": "agy-test",
                "plugin_source_fingerprint": "plugin",
                "plugin_staged_fingerprint": "plugin",
            }
            (run / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            base = {
                "host": "antigravity",
                "model": "model-x",
                "requested_model": "model-x",
                "effort": "high",
                "protocol_revision": 4,
                "protocol_fingerprint": "abc",
                "hallucinations": [],
                "cost": {"wall_seconds": 10.0},
            }
            native = dict(base, case_id="QH-01", trial=1, thalarch=False, task_status="FAIL")
            thalarch = dict(base, case_id="QH-01", trial=1, thalarch=True, task_status="PASS")
            (run / "results" / "QH-01.native.r01.json").write_text(json.dumps(native), encoding="utf-8")
            (run / "results" / "QH-01.thalarch.r01.json").write_text(json.dumps(thalarch), encoding="utf-8")

            public = publish_run.create_public_manifest(run)
            self.assertEqual(public["result_count"], 2)
            self.assertFalse(public["privacy"]["raw_transcripts_included"])
            self.assertEqual(public["aggregate"]["native"]["task_pass_percent"], 0.0)
            self.assertEqual(public["aggregate"]["thalarch"]["task_pass_percent"], 100.0)
            self.assertEqual(public["attestation_sha256"], verify_published_run.canonical_hash(public))
            serialized = json.dumps(public)
            self.assertNotIn(str(run), serialized)


class AblationTests(unittest.TestCase):
    def test_skills_only_variant_disables_every_hook_group(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = {"a": {"enabled": True, "Stop": []}, "b": {"enabled": False}}
            (root / "hooks.json").write_text(json.dumps(payload), encoding="utf-8")
            run_ablation.set_all_hooks_enabled(root, False)
            changed = json.loads((root / "hooks.json").read_text(encoding="utf-8"))
            self.assertFalse(changed["a"]["enabled"])
            self.assertFalse(changed["b"]["enabled"])


class HoldoutTests(unittest.TestCase):
    def test_holdout_case_validation_accepts_quick_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cases.json"
            path.write_text(json.dumps({
                "protocol_revision": 4,
                "cases": [{
                    "id": "HO-01",
                    "title": "hidden",
                    "prompt": "Inspect it.",
                    "files": {"README.md": "fixture"},
                    "success_signal": "Stay grounded",
                }],
            }), encoding="utf-8")
            run_holdout.validate_cases(path)


class HostTemplateTests(unittest.TestCase):
    def test_template_substitution_is_argv_safe(self):
        rendered = render_command(
            ["agent", "--prompt", "{prompt}", "--dir={workspace}", "--model", "{model}"],
            prompt="hello; not a shell",
            workspace=Path("/tmp/example"),
            model="m1",
        )
        self.assertEqual(rendered[2], "hello; not a shell")
        self.assertEqual(rendered[-1], "m1")


class LongBenchTests(unittest.TestCase):
    def test_hidden_test_is_injected_after_agent_and_can_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            run_dir.mkdir()
            task = {
                "id": "LB-UNIT-1",
                "prompt": "Make answer.txt contain 42.",
                "fixture": {"answer.txt": "0\n", "protected.txt": "keep\n"},
                "protected_paths": ["protected.txt"],
                "forbidden_paths": ["secrets/**"],
                "hidden_files": {
                    "hidden_check.py": (
                        "from pathlib import Path\n"
                        "raise SystemExit(0 if Path('answer.txt').read_text().strip() == '42' else 1)\n"
                    )
                },
                "hidden_tests": [{"argv": [sys.executable, "hidden_check.py"], "timeout": 30}],
            }
            script = "from pathlib import Path; Path('answer.txt').write_text('42\\n')"
            command_json = json.dumps([sys.executable, "-c", script])
            row = run_longbench.run_task(
                task,
                host="antigravity",
                model="unit-model",
                command_json=command_json,
                agent_timeout=30,
                run_dir=run_dir,
            )
            self.assertEqual(row["task_status"], "PASS")
            self.assertEqual(row["hidden_files_count"], 1)
            self.assertEqual(row["protected_path_regressions"], [])

    def test_forbidden_edit_fails_even_when_hidden_test_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            run_dir.mkdir()
            task = {
                "id": "LB-UNIT-2",
                "prompt": "Do the task without touching secrets.",
                "fixture": {"answer.txt": "42\n", "secrets/key.txt": "keep\n"},
                "forbidden_paths": ["secrets/**"],
                "hidden_files": {"hidden_check.py": "raise SystemExit(0)\n"},
                "hidden_tests": [{"argv": [sys.executable, "hidden_check.py"]}],
            }
            script = "from pathlib import Path; Path('secrets/key.txt').write_text('changed')"
            row = run_longbench.run_task(
                task,
                host="antigravity",
                model="unit-model",
                command_json=json.dumps([sys.executable, "-c", script]),
                agent_timeout=30,
                run_dir=run_dir,
            )
            self.assertEqual(row["task_status"], "FAIL")
            self.assertEqual(row["forbidden_path_violations"], ["secrets/key.txt"])


if __name__ == "__main__":
    unittest.main()
