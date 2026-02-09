from app.quality.security_scan import heuristic_security_scan


def test_heuristic_security_scan_blocks_rm_rf_root():
    res = heuristic_security_scan(
        name="bad-skill",
        description="does bad things",
        content="Run: sudo rm -rf /",
        url="https://github.com/x/y/blob/main/skills/bad/SKILL.md",
    )
    assert res.block is True
    assert res.severity in {"high", "critical"}
    assert any("destructive" in r.lower() or "rm" in r.lower() for r in res.reasons)


def test_heuristic_security_scan_allows_benign_content():
    res = heuristic_security_scan(
        name="good-skill",
        description="does good things",
        content="# Overview\nThis skill helps format markdown safely.",
        url="https://github.com/x/y/blob/main/skills/good/SKILL.md",
    )
    assert res.ok is True
    assert res.block is False

