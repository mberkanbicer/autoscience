"""Verify Alembic migration chain integrity."""

from pathlib import Path


def test_alembic_revisions_form_single_head():
    versions_dir = Path(__file__).resolve().parents[2] / "alembic" / "versions"
    revisions: dict[str, str | None] = {}

    for path in versions_dir.glob("*.py"):
        if path.name.startswith("__"):
            continue
        text = path.read_text()
        revision = _extract_assignment(text, "revision")
        down_revision = _extract_assignment(text, "down_revision")
        if revision:
            revisions[revision] = down_revision

    assert revisions, "No migration revisions found"

    referenced = {down for down in revisions.values() if down}
    heads = [rev for rev in revisions if rev not in referenced]
    assert len(heads) == 1, f"Expected single head, found {heads}"

    # Walk chain from head to root
    head = heads[0]
    visited = set()
    current: str | None = head
    while current:
        assert current not in visited, f"Cycle detected at {current}"
        visited.add(current)
        current = revisions.get(current)


def _extract_assignment(text: str, name: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(f"{name}:") or stripped.startswith(f"{name} ="):
            value = stripped.split("=", 1)[-1].strip().strip('"').strip("'")
            if value in {"None", "null"}:
                return None
            return value
    return None