# clinvar-proto development notes

clinvar-proto is the **generator** for the `clinvar_proto` package. See [`CONTEXT.md`](CONTEXT.md) for the domain model
and [`README.md`](README.md) for usage and release steps.

## Working norms

Operating directives for Claude (and any agent) in this repo; they counteract default model dispositions. These match
the CPG standard (see `litfetch`).

- **Resist the minimal-diff reflex.** Aim for the correct fix at the right complexity level — not the smallest change
  that hides a symptom, not gold-plated.
- **Fail loudly and early.** Raise on a missing input or precondition; never fall back to a default to limp along.
- **Push back; don't just comply.** When a design, name, or approach seems worse, say so with reasoning. The author owns
  the final call.
- **Investigate before producing.** Read the code and verify constraints first.
- **Ask when unsure** rather than assume intent.

## Repo-specific gotchas

- **The consumable artifact is generated, not committed.** `generated/` and `dist/` are gitignored. Never hand-edit
  generated output — change `clinvar_transforms.yaml` (or re-vendor the XSD) and regenerate. To fix how the schema is
  shaped, the engine is `xsd-former`, not this repo.
- **Never hand-patch the XSD.** It is byte-identical to NCBI's published file and its MD5 is documented in the README; a
  local edit breaks that check. Schema shaping belongs in the transforms.
- **Version lives in `clinvar_transforms.yaml` (`build.version`)**, not in this repo's `pyproject.toml`. That is the
  version `xsdformer` stamps into the wheel and what the release tag must match.
- **`xsd-former` is a build input.** A floor lives in `pyproject.toml`; the exact version is pinned in `uv.lock`.
  Bumping it can change generated output, so re-run the round-trip gate after any bump.
- **The round-trip test builds via the `xsdformer` CLI** (the shipping path) and imports the result in a subprocess —
  because the compiled `*_pb2` registers in a global descriptor pool. Keep that isolation.
- **A new upstream XSD version means a new filename.** `ClinVar_VCV_<n>.xsd` is referenced from the `Makefile`, the
  release workflow, and the round-trip test; update all three when re-vendoring.

## Before committing

- `uv run --group test pytest` — the round-trip gate must pass.
- `uv run --group lint ruff check . && uv run --group lint ruff format --check .`
- `uv lock` if dependencies changed, and commit `uv.lock`.
