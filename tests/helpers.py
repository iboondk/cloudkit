"""Shared helpers for the static CloudKit tests (text and YAML parsing only)."""
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

_BLOCK_RE = re.compile(
    r'^\s*(resource|data|variable|output|module)\s+"([^"]+)"(?:\s+"([^"]+)")?',
    re.MULTILINE,
)


def read(path):
    """Return the text of a file. Relative paths are resolved against ROOT."""
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    return p.read_text(encoding="utf-8")


def hcl_blocks(text, kind, type_=None):
    """Return (label1, label2) tuples for HCL blocks of the given kind.

    kind is one of resource, data, variable, output, module.
    For resource/data blocks, label1 is the type and label2 the name.
    For variable/output/module blocks, label1 is the name and label2 is None.
    If type_ is given, only blocks whose label1 equals type_ are returned.
    """
    found = []
    for match in _BLOCK_RE.finditer(text):
        if match.group(1) != kind:
            continue
        label1, label2 = match.group(2), match.group(3)
        if type_ is not None and label1 != type_:
            continue
        found.append((label1, label2))
    return found


def tf_text(directory):
    """Concatenate every *.tf file in a directory (not recursive), sorted by name."""
    d = Path(directory)
    if not d.is_absolute():
        d = ROOT / d
    return "\n".join(p.read_text(encoding="utf-8") for p in sorted(d.glob("*.tf")))


def balanced_braces(text):
    """Return True when the count of '{' equals the count of '}'."""
    return text.count("{") == text.count("}")


def load_yaml(path):
    """Parse a YAML file with PyYAML and return the Python object."""
    return yaml.safe_load(read(path))
