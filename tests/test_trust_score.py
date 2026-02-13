from app.quality.trust_score import compute_trust_profile


def test_trust_score_high_quality_ok():
    profile = compute_trust_profile(
        quality_score=95,
        is_verified=True,
        is_official=True,
        security_block=False,
        security_severity=None,
        security_indicators=None,
        github_updated_at=None,
    )
    assert profile.level in {"ok", "warning"}
    assert profile.score >= 70


def test_trust_score_security_block_limited():
    profile = compute_trust_profile(
        quality_score=90,
        is_verified=True,
        is_official=True,
        security_block=True,
        security_severity="critical",
        security_indicators=["destructive_rm"],
        github_updated_at=None,
    )
    assert profile.level == "limited"
    assert any(flag.startswith("security:") for flag in profile.flags)


def test_trust_score_low_quality_warning_or_limited():
    profile = compute_trust_profile(
        quality_score=30,
        is_verified=False,
        is_official=False,
        security_block=False,
        security_severity=None,
        security_indicators=None,
        github_updated_at=None,
    )
    assert profile.level in {"warning", "limited"}
    assert "quality:low" in profile.flags
