"""Guard: the generated `_pb2` imports under the protobuf runtime this repo builds against.

protoc bakes its own gencode version into the generated module and the runtime refuses to load it
when the *installed* protobuf is older — `ValidateProtobufRuntimeVersion` raises `VersionError`, so
the failure is an import error in the consumer, not a subtle misparse. The gencode version comes
from whichever protoc runs, which here is the one bundled in `grpcio-tools`; so the `grpcio-tools`
pin and the protobuf floor are coupled, and bumping the former can strand consumers on the latter.

This asserts the coupling holds for the environment the wheel is built and tested in. It does not
assert it for the floor the generated wheel *declares* — see the note on the `grpcio-tools` pin in
`pyproject.toml`.
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys

# The generated module calls `ValidateProtobufRuntimeVersion(Domain.PUBLIC, major, minor, patch, ...)`.
# Read the arguments rather than the neighbouring comment: the call is what the runtime enforces.
_GENCODE_CALL = re.compile(
    r'ValidateProtobufRuntimeVersion\(\s*'
    r'_runtime_version\.Domain\.\w+\s*,\s*'
    r'(?P<major>\d+)\s*,\s*(?P<minor>\d+)\s*,\s*(?P<patch>\d+)\s*,',
)


def _gencode_version(pb2_path: pathlib.Path) -> tuple[int, int, int]:
    match = _GENCODE_CALL.search(pb2_path.read_text('utf-8'))
    if match is None:
        raise AssertionError(f'no ValidateProtobufRuntimeVersion call found in {pb2_path}')
    return int(match['major']), int(match['minor']), int(match['patch'])


def test_generated_pb2_imports_under_the_installed_runtime(built_package: pathlib.Path) -> None:
    """The gencode protoc emitted must load under the protobuf the wheel is tested against.

    Run in a subprocess: importing the generated `_pb2` registers in a global descriptor pool, and
    the round-trip gate does its own import in isolation for the same reason.
    """
    pb2 = built_package / 'clinvar_proto' / 'clinvar_pb2.py'
    gencode = _gencode_version(pb2)

    result = subprocess.run(
        [
            sys.executable,
            '-c',
            'import sys; sys.path.insert(0, sys.argv[1]);'
            ' from clinvar_proto import clinvar_pb2;'
            ' import google.protobuf as p; print(p.__version__)',
            str(built_package),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f'the generated clinvar_pb2 (gencode {".".join(map(str, gencode))}) does not import under the '
        f'installed protobuf runtime. Either lower the grpcio-tools pin so protoc emits older gencode, '
        f'or raise the protobuf pin.\n{result.stderr}'
    )
