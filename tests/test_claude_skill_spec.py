from app.quality.claude_skill_spec import validate_claude_skill_frontmatter


def test_lax_allows_nonconforming_name_as_warning():
    res = validate_claude_skill_frontmatter(
        metadata={"name": "Bad Name"},
        body="Hello world.",
        canonical_url="https://github.com/o/r/blob/main/skills/bad-name/SKILL.md",
        frontmatter_raw="name: Bad Name",
        frontmatter_error=None,
        profile="lax",
    )
    assert res.ok is True
    assert "invalid_name_format" in res.warnings


def test_strict_rejects_nonconforming_name():
    res = validate_claude_skill_frontmatter(
        metadata={"name": "Bad Name"},
        body="Hello world.",
        canonical_url="https://github.com/o/r/blob/main/skills/bad-name/SKILL.md",
        frontmatter_raw="name: Bad Name",
        frontmatter_error=None,
        profile="strict",
    )
    assert res.ok is False
    assert "invalid_name_format" in res.errors


def test_description_fallback_from_body():
    res = validate_claude_skill_frontmatter(
        metadata={"name": "ok-name"},
        body="# Title\n\nThis is the first paragraph.\n\nMore.",
        canonical_url="https://github.com/o/r/blob/main/skills/ok-name/SKILL.md",
        frontmatter_raw="name: ok-name",
        frontmatter_error=None,
        profile="lax",
    )
    assert res.derived_description == "This is the first paragraph."
    assert "description_missing_used_body_fallback" in res.warnings


def test_allowed_tools_normalization_from_string():
    res = validate_claude_skill_frontmatter(
        metadata={"name": "ok-name", "allowed-tools": "Read, Grep,  Bash"},
        body="Hello.",
        canonical_url="https://github.com/o/r/blob/main/skills/ok-name/SKILL.md",
        frontmatter_raw="name: ok-name\nallowed-tools: Read, Grep,  Bash",
        frontmatter_error=None,
        profile="lax",
    )
    assert res.ok is True
    assert res.normalized["allowed-tools"] == ["Read", "Grep", "Bash"]


def test_context_agent_checks():
    res = validate_claude_skill_frontmatter(
        metadata={"name": "ok-name", "agent": "Foo"},
        body="Hello.",
        canonical_url="https://github.com/o/r/blob/main/skills/ok-name/SKILL.md",
        frontmatter_raw="name: ok-name\nagent: Foo",
        frontmatter_error=None,
        profile="strict",
    )
    assert res.ok is True
    assert "agent_requires_context_fork" in res.warnings

