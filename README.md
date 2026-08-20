# clinvar-proto

Generates **`clinvar_proto`** — a typed Python package for parsing NCBI ClinVar
VCV XML into protobuf and pydantic models — from the ClinVar VCV XSD.

This repository is the **generator**, not the package. It holds the inputs
(`ClinVar_VCV_2.6.xsd`, `clinvar_transforms.yaml`) and drives
[`xsd-former`](https://github.com/populationgenomics/xsd-former) (the
`xsdformer` CLI) to emit the `clinvar_proto` source tree, which is then built
into a wheel and published to PyPI. The generated tree (`generated/`) and build
outputs (`dist/`) are gitignored — only the inputs are version-controlled.

Sibling to [`pubmed-proto`](https://github.com/populationgenomics/pubmed-proto);
same generate-on-demand model.

## Consuming `clinvar_proto`

Depend on the published wheel, not this repo:

```
pip install clinvar_proto      # or: uv add clinvar_proto
```

```python
from lxml import etree
from clinvar_proto import xml_converter, pydantic_converter, models

tree = etree.parse('clinvar_release.xml')
archive_el = tree.getroot().find('VariationArchive')

proto = xml_converter.VariationArchiveType(archive_el)  # XML -> protobuf
model = pydantic_converter.VariationArchiveType_from_proto(proto)  # protobuf -> pydantic
json_str = model.model_dump_json()  # pydantic -> JSON
```

The converters take any ElementTree-like element, so `lxml` is the consumer's
choice, not a dependency of the wheel (`clinvar_proto` needs only `protobuf` and
`pydantic`). Release files are large, so consumers normally stream them with
`lxml.etree.iterparse` on `VariationArchive` and convert one element at a time.

The package exposes four modules (all typed; ships `py.typed`):

| module               | purpose                                                  |
| -------------------- | -------------------------------------------------------- |
| `clinvar_pb2`        | compiled protobuf messages (`VariationArchiveType`, …)    |
| `models`             | pydantic models mirroring the protobuf schema             |
| `xml_converter`      | ClinVar XML → protobuf (per-message factory funcs)        |
| `pydantic_converter` | protobuf ↔ pydantic (`X_from_proto` / `X_to_proto`)       |

## Developing the generator

Requires [`uv`](https://docs.astral.sh/uv/).

```
make generate   # XSD + transforms -> generated/clinvar_proto/
make build      # generate, then build the wheel into dist/
make clean      # remove generated/ and dist/
uv run --group test pytest   # round-trip gate over real ClinVar records
```

Shaping the output is done in **`clinvar_transforms.yaml`** — inlining single-
child wrappers, flattening list wrappers, and attaching documentation comments
to the generated messages and fields. See the
[`xsd-former`](https://github.com/populationgenomics/xsd-former) docs for the
transform reference.

## Provenance & attribution

`ClinVar_VCV_2.6.xsd` is the **NCBI ClinVar VCV XSD**, version `2.6`
(dated 2026-02-26):

<https://ftp.ncbi.nlm.nih.gov/pub/clinvar/xsd_public/ClinVar_VCV_2.6.xsd>

The vendored file is byte-identical to upstream
(MD5 `a7b65e5a166dc5f36a7eea9127d56f4e`, matching NCBI's published
`ClinVar_VCV_2.6.xsd.md5`). NCBI ClinVar data and schemas are U.S. Government
works and public domain in the United States; the MIT `LICENSE` in this repo
covers CPG's own files (transforms, generator wiring, tests), not the NCBI XSD.

Courtesy of the U.S. National Library of Medicine. NLM/NCBI does not endorse
this package. The vendored XSD and the ClinVar records under `tests/records/`
are pinned snapshots and do not necessarily reflect the most current data
available from NCBI — fetch from NCBI directly for current data.

The XSD is **vendored deliberately, not fetched at build time**: pinning the
exact bytes keeps the generated schema reproducible, and NCBI's XSD version is
bumped in place under a new filename rather than being immutable per release.
When NCBI publishes a new version, re-vendor the file from
<https://ftp.ncbi.nlm.nih.gov/pub/clinvar/xsd_public/>, point the `Makefile` and
tests at it, regenerate, and run the round-trip gate.

## Releasing

The published version is **`build.version` in `clinvar_transforms.yaml`** (what
`xsdformer` stamps into the wheel). To release:

1. Bump `build.version` in `clinvar_transforms.yaml`.
2. Publish a GitHub Release tagged `vX.Y.Z` matching that version.

The `release` workflow generates, builds, and publishes to PyPI via Trusted
Publishing (OIDC). It fails if the tag and `build.version` disagree.
