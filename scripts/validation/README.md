# Validation tooling

Repository validation lives here so the project root stays focused on the public entry points.

Run validators from the repository root and pass `.` as the project root:

```bash
python scripts/validation/validate_thalarch.py .
python scripts/validation/validate_autoresearch.py .
python scripts/validation/validate_hard_gates.py .
python scripts/validation/validate_adapters.py .
python scripts/validation/validate_cross_host_policy.py .
python scripts/validation/validate_benchmarks.py .
```

The scripts intentionally resolve project files from the explicit root argument rather than from their own directory. This keeps them relocatable without changing the repository-relative checks they perform.
