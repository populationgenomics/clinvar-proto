# clinvar-proto

Generates the `clinvar_proto` Python package — protobuf message classes and
an lxml→proto converter for NCBI ClinVar VCV records — from the vendored XSD
via [`xsd-former`](../xsd-former). Sibling to [`pubmed-proto`](../pubmed-proto);
same generate-on-demand model.

## Layout

- `ClinVar_VCV_2.6.xsd` — vendored, pinned schema (the data contract). Re-vendor
  from `http://ftp.ncbi.nlm.nih.gov/pub/clinvar/xsd_public/` when NCBI bumps the
  version, then regenerate.
- `clinvar_transforms.yaml` — `xsd-former` config: the `build:` section sets the
  package name/namespace; `comments:` annotate the generated proto; structural
  flags inline wrappers and flatten list-wrappers.
- `generated/` — produced output (gitignored): `clinvar_proto/` package with
  `clinvar_pb2.py`, `clinvar.proto`, `xml_converter.py`.

## Usage

```sh
make generate   # XSD + transforms -> generated/clinvar_proto/
make build      # -> dist/*.whl
```

Consumers depend on it via path (see `clinvar-mirror`):

```python
from clinvar_proto import clinvar_pb2, xml_converter
pb = xml_converter.VariationArchiveType(elem)   # elem from lxml.iterparse
```
