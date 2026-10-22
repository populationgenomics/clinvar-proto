"""Record gate over real ClinVar VCV records.

This is clinvar-proto's release safety net: it builds the package from *this
repo's* ``ClinVar_VCV_2.6.xsd`` + ``clinvar_transforms.yaml`` using the shipping
path (the ``xsdformer`` CLI, exactly what ``make build`` runs), then converts
real NCBI ClinVar VCV records with the generated ``xml_converter`` and checks
that each ``VariationArchive`` comes out under the accession and variation ID
its XML carries, with the classified or included record the XML has.

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
def test_clinvar_record_converts(record: pathlib.Path, built_package: pathlib.Path) -> None:
    # Run in a subprocess so the dynamically compiled `*_pb2` (a global
    # descriptor-pool registration) stays isolated from the test process.
    script = f"""
import sys
sys.path.insert(0, {str(built_package)!r})
from lxml import etree
from clinvar_proto import xml_converter

tree = etree.parse({str(record)!r})
archive_el = tree.getroot().find("VariationArchive")
assert archive_el is not None
proto = xml_converter.VariationArchiveType(archive_el)

assert proto.accession == archive_el.get("Accession"), 'accession differs from the XML'
assert proto.variation_id == int(archive_el.get("VariationID")), 'variation ID differs from the XML'
for tag, field in (("ClassifiedRecord", "classified_record"), ("IncludedRecord", "included_record")):
    assert proto.HasField(field) == (archive_el.find(tag) is not None), f'{{field}} presence differs from the XML'
"""
    result = subprocess.run(
        [sys.executable, '-c', script],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
