"""Round-trip gate over real ClinVar VCV records.

This is clinvar-proto's release safety net: it builds the package from *this
repo's* ``ClinVar_VCV_2.6.xsd`` + ``clinvar_transforms.yaml`` using the shipping
path (the ``xsdformer`` CLI, exactly what ``make build`` runs), then checks that
real NCBI ClinVar VCV records survive the full generated suite:

* ``XML -> proto -> pydantic -> proto`` is identical in the proto, and
* ``proto -> pydantic -> JSON -> pydantic`` round-trips in pydantic.

An XSD or transform edit that breaks the generated wheel fails here before it
can be published. Fixtures in ``records/`` are real ``efetch`` output, chosen to
cover the record shapes the schema branches on: a classified simple allele, a
haplotype, a diplotype (genotype), an included record, and a record carrying
somatic/oncogenicity classifications.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

import pytest

_RECORDS_DIR = pathlib.Path(__file__).parent / 'records'
_RECORDS = sorted(_RECORDS_DIR.glob('*.xml'))

# `built_package` is a session fixture in conftest.py, shared with the other generated-output gates.


def test_records_present() -> None:
    assert _RECORDS, f'no ClinVar record fixtures found in {_RECORDS_DIR}'


@pytest.mark.parametrize('record', _RECORDS, ids=lambda p: p.stem)
def test_clinvar_record_roundtrip(record: pathlib.Path, built_package: pathlib.Path) -> None:
    # Run in a subprocess so the dynamically compiled `*_pb2` (a global
    # descriptor-pool registration) stays isolated from the test process.
    script = f"""
import sys
sys.path.insert(0, {str(built_package)!r})
from lxml import etree
from clinvar_proto import xml_converter, pydantic_converter, models

tree = etree.parse({str(record)!r})
archive_el = tree.getroot().find("VariationArchive")
assert archive_el is not None
proto = xml_converter.VariationArchiveType(archive_el)

# XML -> proto -> pydantic -> proto is identical in the proto.
model = pydantic_converter.VariationArchiveType_from_proto(proto)
assert pydantic_converter.VariationArchiveType_to_proto(model) == proto

# proto -> pydantic -> JSON -> pydantic round-trips in pydantic.
restored = models.VariationArchiveType.model_validate_json(model.model_dump_json())
assert restored == model
"""
    result = subprocess.run(
        [sys.executable, '-c', script],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
