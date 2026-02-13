
"""Skills API."""

import uuid
from typing import Annotated, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import case, desc, func, literal, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.api.cache_headers import (
    PUBLIC_DETAIL_CACHE,
    PUBLIC_SEARCH_CACHE,
    REDIS_TTL_DETAIL,
    REDIS_TTL_SEARCH,
    set_public_cache,
)
from app.models.category import Category
from app.models.skill import Skill
from app.models.skill_popularity import SkillPopularity
from app.models.skill_tag import SkillTag
from app.models.tag import Tag
from app.repos.public_filters import is_public_skill_url, public_skill_conditions
from app.repos.skill_repo import SkillRepo
from app.api.response_cache import set_cached_response, try_cached_response
from app.schemas.common import Page
from app.schemas.skill import SkillDetail, SkillListItem

router = APIRouter()

SearchMode = Literal["keyword", "vector", "hybrid"]


def _parse_search_weights(mode: SearchMode, raw_weights: Optional[str]) -> tuple[float, float]:
    """Parse and normalize keyword/vector weights."""
    defaults: dict[SearchMode, tuple[float, float]] = {
        "keyword": (1.0, 0.0),
        "vector": (0.0, 1.0),
        "hybrid": (0.45, 0.55),
    }
    if mode != "hybrid":
        return defaults[mode]
    if not raw_weights:
        return defaults["hybrid"]

    raw = raw_weights.strip()
    if not raw:
        return defaults["hybrid"]

    keyword_weight: Optional[float] = None
    vector_weight: Optional[float] = None

    try:
        if ":" in raw:
            for part in raw.split(","):
                token = part.strip()
                if not token:
                    continue
                key, value = token.split(":", maxsplit=1)
                parsed = float(value.strip())
                key_normalized = key.strip().lower()
                if key_normalized in {"keyword", "k"}:
                    keyword_weight = parsed
                elif key_normalized in {"vector", "v"}:
                    vector_weight = parsed
                else:
                    raise ValueError(f"Unknown weight key: {key}")
        else:
            values = [segment.strip() for segment in raw.split(",") if segment.strip()]
            if len(values) != 2:
                raise ValueError("weights must contain two numeric values")
            keyword_weight = float(values[0])
            vector_weight = float(values[1])
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail="Invalid weights format. Use '0.45,0.55' or 'keyword:0.45,vector:0.55'.",
        ) from exc

    if keyword_weight is None or vector_weight is None:
        raise HTTPException(
            status_code=422,
            detail="Both keyword and vector weights are required for hybrid mode.",
        )
    if keyword_weight < 0 or vector_weight < 0:
        raise HTTPException(status_code=422, detail="weights must be non-negative.")

    total = keyword_weight + vector_weight
    if total <= 0:
        raise HTTPException(status_code=422, detail="weights total must be > 0.")
    return keyword_weight / total, vector_weight / total


def _build_match_reason(
    active_mode: SearchMode,
    keyword_score: float,
    vector_score: float,
    fallback_used: bool,
) -> str:
    """Build a concise explanation for why this row matched."""
    if fallback_used:
        if keyword_score > 0:
            return "keyword match (vector fallback)"
        return "keyword fallback"
    if active_mode == "vector":
        return "semantic vector match"
    if active_mode == "hybrid":
        if keyword_score > 0 and vector_score > 0:
            return "hybrid: keyword + vector"
        if keyword_score > 0:
            return "hybrid: keyword-heavy"
        return "hybrid: vector-heavy"
    if keyword_score > 0:
        return "keyword relevance"
    return "sorted result"


def _resolve_active_mode(
    requested_mode: SearchMode,
    query_text: str,
    embedding_available: bool,
) -> tuple[SearchMode, bool]:
    """Return active mode and whether vector fallback was used."""
    if query_text and requested_mode in {"vector", "hybrid"} and not embedding_available:
        return "keyword", True
    return requested_mode, False


def is_public_skill(skill: Skill) -> bool:
    """Apply public visibility policy to a loaded skill row."""
    if not skill.is_official or not skill.is_verified:
        return False
    return is_public_skill_url(skill.url)


def _skill_list_page_payload(page_result: Page[SkillListItem]) -> dict:
    """Serialize Page[SkillListItem] safely when rows came from ORM objects."""
    return {
        "items": [SkillListItem.model_validate(item).model_dump(mode="json") for item in page_result.items],
        "total": page_result.total,
        "page": page_result.page,
        "size": page_result.size,
        "pages": page_result.pages,
    }


async def _list_skills_impl(
    db: AsyncSession,
    *,
    q: Optional[str],
    category: Optional[str],
    tags: Optional[list[str]],
    sort: str,
    page: int,
    size: int,
    mode: SearchMode,
    weights: Optional[str],
) -> Page[SkillListItem]:
    query_text = (q or "").strip()
    keyword_weight, vector_weight = _parse_search_weights(mode, weights)

    query_embedding: Optional[list[float]] = None
    fallback_to_keyword = False
    active_mode: SearchMode = mode

    if query_text and mode in {"vector", "hybrid"}:
        from app.llm.embeddings import generate_embedding

        try:
            query_embedding = generate_embedding(query_text)
        except Exception:
            query_embedding = None

    active_mode, fallback_to_keyword = _resolve_active_mode(
        requested_mode=mode,
        query_text=query_text,
        embedding_available=bool(query_embedding),
    )
    if active_mode == "keyword":
        keyword_weight, vector_weight = 1.0, 0.0

    keyword_match = literal(True)
    keyword_score_expr = literal(0.0)
    if query_text:
        like = f"%{query_text}%"
        name_match = Skill.name.ilike(like)
        slug_match = Skill.slug.ilike(like)
        description_match = Skill.description.ilike(like)
        summary_match = Skill.summary.ilike(like)
        content_match = Skill.content.ilike(like)
        tag_match = (
            select(SkillTag.skill_id)
            .join(Tag, SkillTag.tag_id == Tag.id)
            .where(
                SkillTag.skill_id == Skill.id,
                or_(Tag.name.ilike(like), Tag.slug.ilike(like)),
            )
            .exists()
        )
        keyword_match = or_(
            name_match,
            slug_match,
            description_match,
            summary_match,
            content_match,
            tag_match,
        )
        keyword_score_expr = (
            case((name_match, 1.00), else_=0.0)
            + case((slug_match, 0.90), else_=0.0)
            + case((summary_match, 0.75), else_=0.0)
            + case((description_match, 0.65), else_=0.0)
            + case((tag_match, 0.80), else_=0.0)
            + case((content_match, 0.20), else_=0.0)
        )

    vector_score_expr = literal(0.0)
    if query_text and query_embedding:
        vector_score_expr = func.coalesce(
            1.0 / (1.0 + Skill.embedding.l2_distance(query_embedding)),
            0.0,
        )

    combined_score_expr = (
        (keyword_score_expr * keyword_weight) + (vector_score_expr * vector_weight)
    ).label("combined_score")
    popularity_score_expr = func.coalesce(SkillPopularity.score, 0.0).label("popularity_score")
    trust_rank_expr = case(
        (Skill.trust_level == "ok", 2),
        (Skill.trust_level == "warning", 1),
        else_=0,
    ).label("trust_rank")
    trust_score_expr = func.coalesce(Skill.trust_score, 0.0).label("trust_score_rank")

    stmt = (
        select(
            Skill,
            keyword_score_expr.label("keyword_score"),
            vector_score_expr.label("vector_score"),
            combined_score_expr,
            popularity_score_expr,
            trust_rank_expr,
            trust_score_expr,
        )
        .where(*public_skill_conditions())
        .where(
            or_(
                Skill.trust_level.is_(None),
                Skill.trust_level != "limited",
                Skill.trust_score >= 35.0,
            )
        )
        .outerjoin(Skill.popularity)
    )

    if category:
        stmt = stmt.join(Skill.category).where(Category.slug == category)
    if tags:
        tag_filter_exists = (
            select(SkillTag.skill_id)
            .join(Tag, SkillTag.tag_id == Tag.id)
            .where(
                SkillTag.skill_id == Skill.id,
                Tag.slug.in_(tags),
            )
            .exists()
        )
        stmt = stmt.where(tag_filter_exists)

    if query_text:
        if active_mode == "keyword":
            stmt = stmt.where(keyword_match)
        elif active_mode == "vector":
            stmt = stmt.where(Skill.embedding.is_not(None))
        else:
            stmt = stmt.where(or_(keyword_match, Skill.embedding.is_not(None)))

        stmt = stmt.order_by(
            desc(combined_score_expr),
            desc(trust_rank_expr),
            desc(trust_score_expr),
            desc(popularity_score_expr),
            desc(Skill.updated_at),
            Skill.id.asc(),
        )
    else:
        if sort == "newest":
            stmt = stmt.order_by(desc(Skill.created_at), desc(Skill.updated_at), Skill.id.asc())
        elif sort == "oldest":
            stmt = stmt.order_by(Skill.created_at.asc(), Skill.id.asc())
        else:
            stmt = stmt.order_by(
                desc(popularity_score_expr),
                desc(trust_rank_expr),
                desc(trust_score_expr),
                desc(Skill.updated_at),
                Skill.id.asc(),
            )

    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total = int((await db.execute(count_stmt)).scalar_one() or 0)
    total_pages = (total + size - 1) // size if total > 0 else 0

    stmt = (
        stmt.offset((page - 1) * size)
        .limit(size)
        .options(
            selectinload(Skill.category),
            selectinload(Skill.tag_associations).selectinload(SkillTag.tag),
            selectinload(Skill.popularity),
            selectinload(Skill.source_links),
        )
    )
    rows = (await db.execute(stmt)).all()

    items: list[Skill] = []
    for row in rows:
        skill = row[0]
        keyword_score_value = float(row[1] or 0.0)
        vector_score_value = float(row[2] or 0.0)
        if query_text:
            skill.match_reason = _build_match_reason(
                active_mode=active_mode,
                keyword_score=keyword_score_value,
                vector_score=vector_score_value,
                fallback_used=fallback_to_keyword,
            )
        else:
            skill.match_reason = f"sorted by {sort}"
        items.append(skill)

    return Page(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=total_pages,
    )


@router.get("", response_model=Page[SkillListItem])
async def list_skills(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    q: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[list[str]] = Query(None),
    sort: str = "popularity",
    mode: SearchMode = Query("hybrid"),
    weights: Optional[str] = Query(
        None,
        description="Hybrid weights. Example: '0.45,0.55' or 'keyword:0.45,vector:0.55'",
    ),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    limit: Optional[int] = Query(None, ge=1, le=100),
):
    """List skills with keyword/vector/hybrid search options."""
    set_public_cache(response, PUBLIC_SEARCH_CACHE)
    cached = await try_cached_response(
        request=request,
        namespace="skills:list",
        cache_control=PUBLIC_SEARCH_CACHE,
    )
    if cached is not None:
        return cached
    effective_size = limit if limit is not None else size
    page_result = await _list_skills_impl(
        db,
        q=q,
        category=category,
        tags=tags,
        sort=sort,
        page=page,
        size=effective_size,
        mode=mode,
        weights=weights,
    )
    payload = _skill_list_page_payload(page_result)
    await set_cached_response(
        request=request,
        namespace="skills:list",
        payload=payload,
        ttl_seconds=REDIS_TTL_SEARCH,
    )
    response.headers["X-Cache"] = "MISS"
    return payload


@router.get("/search/ai", response_model=Page[SkillListItem])
async def ai_search_skills(
    request: Request,
    response: Response,
    q: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """Backward-compatible endpoint for semantic search."""
    set_public_cache(response, PUBLIC_SEARCH_CACHE)
    cached = await try_cached_response(
        request=request,
        namespace="skills:ai-search",
        cache_control=PUBLIC_SEARCH_CACHE,
    )
    if cached is not None:
        return cached
    page_result = await _list_skills_impl(
        db,
        q=q,
        category=None,
        tags=None,
        sort="popularity",
        page=page,
        size=size,
        mode="hybrid",
        weights=None,
    )
    payload = _skill_list_page_payload(page_result)
    await set_cached_response(
        request=request,
        namespace="skills:ai-search",
        payload=payload,
        ttl_seconds=REDIS_TTL_SEARCH,
    )
    response.headers["X-Cache"] = "MISS"
    return payload


@router.get("/{id}", response_model=SkillDetail)
async def get_skill(
    request: Request,
    response: Response,
    id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get skill details."""
    set_public_cache(response, PUBLIC_DETAIL_CACHE)
    cached = await try_cached_response(
        request=request,
        namespace="skills:detail",
        cache_control=PUBLIC_DETAIL_CACHE,
    )
    if cached is not None:
        return cached
    repo = SkillRepo(db)
    skill = await repo.get_skill(id)
    if not skill or not is_public_skill(skill):
        raise HTTPException(status_code=404, detail="Skill not found")
    payload = SkillDetail.model_validate(skill).model_dump(mode="json")
    await set_cached_response(
        request=request,
        namespace="skills:detail",
        payload=payload,
        ttl_seconds=REDIS_TTL_DETAIL,
    )
    response.headers["X-Cache"] = "MISS"
    return payload
