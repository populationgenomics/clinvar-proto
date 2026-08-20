"""Guard: the generated schema's field and enum numbers match the committed lock.

Why this exists, and why it is not a change detector: proto field numbers *are* the wire format.
`xsdformer` assigns them positionally, so an upstream XSD that inserts one element renumbers every
later field in that type, and an engine bump can do the same. A consumer that vendored the previous
`.proto`, or that persisted messages, then mis-reads those fields with no error — protobuf cannot
detect a renumber, because the bytes stay valid for the new interpretation.

So the invariant is not "the numbers are these values" but "the numbers did not move without anyone
deciding they should". Renumbering stays possible; it stops being *silent*.

See populationgenomics/xsd-former#30 for the engine-level fix (carry numbers forward across
regeneration, reserving retired ones), which would make this guard redundant for insertions.
"""

from __future__ import annotations

import pathlib

import field_numbers

# The VCV schema numbers ~1055 fields and enum members. A floor well under that catches a
# truncated or half-written lock without pinning the exact count, which every legitimate
# schema addition would otherwise change.
_MIN_LOCK_ENTRIES = 1000


def test_lock_is_not_vacuous() -> None:
    """A truncated or empty lock would make the comparison below pass trivially."""
    locked = field_numbers.load_lock()
    assert len(locked) > _MIN_LOCK_ENTRIES, f'lock has only {len(locked)} entries; expected the full VCV schema'


def test_field_numbers_match_the_lock(generated_proto: pathlib.Path) -> None:
    current = field_numbers.extract(generated_proto)
    locked = field_numbers.load_lock()

    moved = {k: (locked[k], current[k]) for k in locked.keys() & current.keys() if locked[k] != current[k]}
    added = sorted(current.keys() - locked.keys())
    removed = sorted(locked.keys() - current.keys())

    # Renumbering an existing field is the wire break; report it on its own, first and in full.
    assert not moved, (
        'field/enum numbers moved — this is a WIRE-INCOMPATIBLE change; a consumer reading the '
        'previous numbering will silently mis-assign these values:\n'
        + '\n'.join(f'  {k}: {was} -> {now}' for k, (was, now) in sorted(moved.items()))
        + '\nIf the renumber is intended, run `make lock-field-numbers` and review the lock diff.'
    )
    assert not (added or removed), (
        'the generated schema gained or lost fields without the lock being updated:\n'
        + ''.join(f'  + {k}\n' for k in added)
        + ''.join(f'  - {k}\n' for k in removed)
        + 'Run `make lock-field-numbers` and review the lock diff.'
    )
