"""Shared fixtures: the generated package, built once via the shipping path.

`xsdformer build` is what `make build` and the release workflow run, so every gate here tests the
artifact that would actually be published rather than a re-derivation of it.
"""

from __future__ import annotations

import pathlib
import subprocess

import pytest

REPO_ROOT = pathlib.Path(__file__).parents[1]
SCHEMA = REPO_ROOT / 'ClinVar_VCV_2.6.xsd'
TRANSFORMS = REPO_ROOT / 'clinvar_transforms.yaml'


@pytest.fixture(scope='session')
def built_package(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """Generate the package once per session via the xsdformer CLI; return the import root."""
    out_dir = tmp_path_factory.mktemp('clinvar_build')
    subprocess.run(
        [
            'xsdformer',
            'build',
            str(SCHEMA),
            '--transforms',
            str(TRANSFORMS),
            '--out-dir',
            str(out_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return out_dir


@pytest.fixture(scope='session')
def generated_proto(built_package: pathlib.Path) -> pathlib.Path:
    """The generated `.proto` inside the built package."""
    proto = built_package / 'clinvar_proto' / 'clinvar.proto'
    if not proto.is_file():
        raise AssertionError(f'generated proto missing at {proto}')
    return proto
