"""Extract the generated schema's field/enum numbering, and maintain the committed lock.

Proto field numbers are the wire contract: a consumer that vendors the generated `.proto`, or
serializes messages with the wheel, is broken by a renumber in a way protobuf cannot detect at
runtime — a reader parsing a moved number silently mis-assigns the value. `xsdformer` assigns
numbers positionally, in schema document order, so inserting one element upstream shifts every
later field in that type (populationgenomics/xsd-former#30).

`field_numbers.lock.json` is the committed record of the current numbering. The guard in
`test_field_numbers.py` regenerates and compares against it, so a renumber becomes a visible,
reviewed diff instead of a silent wire break.

Regenerate the lock deliberately, after deciding a renumber is acceptable:

    make lock-field-numbers

The numbering is read from a `FileDescriptorProto` compiled *without* `--include_source_info`,
which carries no comments — so a comment-only edit to the transforms cannot move it.
"""

from __future__ import annotations

import importlib.resources
import json
import pathlib
import sys
import tempfile

from google.protobuf import descriptor_pb2
from grpc_tools import protoc

_REPO_ROOT = pathlib.Path(__file__).parents[1]
LOCK_PATH = _REPO_ROOT / 'field_numbers.lock.json'


def _compile(proto_path: pathlib.Path) -> descriptor_pb2.FileDescriptorProto:
    """Compile one `.proto` to its `FileDescriptorProto` (no source info, hence no comments)."""
    well_known = str(importlib.resources.files('grpc_tools') / '_proto')
    with tempfile.TemporaryDirectory() as tmp:
        out = pathlib.Path(tmp) / 'descriptor.pb'
        rc = protoc.main(
            [
                'protoc',
                f'-I{proto_path.parent}',
                f'-I{well_known}',
                f'--descriptor_set_out={out}',
                '--include_imports',
                proto_path.name,
            ]
        )
        if rc != 0:
            raise RuntimeError(f'protoc failed on {proto_path}')
        descriptor_set = descriptor_pb2.FileDescriptorSet()
        descriptor_set.ParseFromString(out.read_bytes())
    for file_proto in descriptor_set.file:
        if file_proto.name == proto_path.name:
            return file_proto
    raise RuntimeError(f'{proto_path.name} missing from the compiled descriptor set')


def extract(proto_path: pathlib.Path) -> dict[str, int]:
    """Map every field and enum member to its number, keyed by fully-qualified path."""
    file_proto = _compile(proto_path)
    numbering: dict[str, int] = {}

    def enum_members(container: object, prefix: str) -> None:
        for enum in container.enum_type:  # type: ignore[attr-defined]
            for value in enum.value:
                numbering[f'{prefix}.{enum.name}.{value.name}'] = value.number

    def message(msg: descriptor_pb2.DescriptorProto, prefix: str) -> None:
        path = f'{prefix}.{msg.name}'
        for field in msg.field:
            numbering[f'{path}.{field.name}'] = field.number
        enum_members(msg, path)
        for nested in msg.nested_type:
            message(nested, path)

    for msg in file_proto.message_type:
        message(msg, file_proto.package)
    enum_members(file_proto, file_proto.package)
    return dict(sorted(numbering.items()))


def write_lock(proto_path: pathlib.Path) -> None:
    """Overwrite the committed lock from `proto_path`."""
    numbering = extract(proto_path)
    LOCK_PATH.write_text(json.dumps(numbering, indent=2, sort_keys=True) + '\n', 'utf-8')
    print(f'wrote {LOCK_PATH.name}: {len(numbering)} numbered entries')


def load_lock() -> dict[str, int]:
    """Read the committed lock. Raises if it is absent — the guard must never pass vacuously."""
    if not LOCK_PATH.is_file():
        raise FileNotFoundError(f'{LOCK_PATH} is missing; regenerate it with `make lock-field-numbers`')
    return json.loads(LOCK_PATH.read_text('utf-8'))


if __name__ == '__main__':
    write_lock(pathlib.Path(sys.argv[1]))
