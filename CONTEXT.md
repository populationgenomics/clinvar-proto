# clinvar-proto

clinvar-proto owns *the shape of the `clinvar_proto` package*: which ClinVar VCV
XML elements survive into the schema, how they are named, and how they are
documented. It does **not** own the generation engine (that is `xsd-former`) nor
how consumers store, index, or query the parsed records.

## Language

**Generator** (this repo):
The inputs and build wiring that produce the package — `ClinVar_VCV_2.6.xsd`,
`clinvar_transforms.yaml`, `Makefile`, `pyproject.toml`. Its own distribution is
`clinvar-proto-generator`; it is never published.
*Avoid*: "the package" (that is the generated artifact, below).

**Generated package** (`clinvar_proto`):
The published, consumable artifact — protobuf + pydantic models + converters,
emitted under `generated/` and built into a wheel. Gitignored; reproduced from
the inputs on every build.
*Avoid*: "clinvar-proto" (that is the generator repo).

**Engine** (`xsd-former` / the `xsdformer` CLI):
The external tool that turns an XSD + transform config into the generated
package. Constrained by a floor in `pyproject.toml` and pinned to an exact
version in `uv.lock`; upgrading it can change generated output, so it is treated
as a build input.

**Transforms** (`clinvar_transforms.yaml`):
The single source of truth for the schema's shape *and* its version
(`build.version`). Inlines single-child wrappers, flattens list wrappers, and
carries the `comments:` block — hand-written documentation for ClinVar's
classification vocabularies (star ratings, ACMG/AMP, oncogenicity, somatic
tiers) that the XSD does not supply. That prose is the repo's main asset.

**VCV** (Variation-Centric Version):
ClinVar's variant-centric aggregation — one `VariationArchive` per variation,
holding the aggregate classifications plus every contributing SCV. This repo
models VCV only; the submission-centric (RCV/SCV-only) release schemas are out
of scope.

## Invariants

- The generated tree and `dist/` are never committed — only inputs are.
- The published version is `build.version` in the transforms file, not the
  generator's own `pyproject.toml` version. The release tag must match it.
- The vendored XSD stays byte-identical to the upstream NCBI file, so the
  published MD5 verifies it. Never hand-patch the schema; express changes in
  the transforms.
- `uv.lock` is committed: the artifact is only reproducible because the exact
  engine version is pinned there.
- The round-trip gate (`tests/`) builds from the real inputs and must pass
  before a release — it is what stops an XSD/transform edit shipping a broken
  wheel. Its fixtures deliberately span the record shapes the schema branches
  on (simple allele, haplotype, diplotype, included record, somatic).
