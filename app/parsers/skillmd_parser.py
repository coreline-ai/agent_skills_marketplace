"""SKILL.md Parser."""

import re
import yaml
from typing import Any, Optional

from app.models.category_alias import CategoryAlias

# Frontmatter at file start:
# ---
# <yaml>
# ---
FRONTMATTER_PATTERN = re.compile(r"\A---\s*\r?\n(.*?)\r?\n---\s*(?:\r?\n|\Z)", re.DOTALL)

def parse_skill_md(content: str) -> dict[str, Any]:
    """Parse SKILL.md content, extracting frontmatter."""
    match = FRONTMATTER_PATTERN.match(content)
    
    metadata = {}
    markdown_content = content
    frontmatter_raw: Optional[str] = None
    frontmatter_error: Optional[str] = None
    
    if match:
        try:
            yaml_content = match.group(1)
            frontmatter_raw = yaml_content
            loaded = yaml.safe_load(yaml_content) or {}
            metadata = loaded if isinstance(loaded, dict) else {}
            if loaded is not None and not isinstance(loaded, dict):
                frontmatter_error = "frontmatter_must_be_mapping"
            markdown_content = content[match.end():].strip()
        except yaml.YAMLError:
            frontmatter_raw = match.group(1)
            frontmatter_error = "invalid_frontmatter"
            print("YAML Error parsing frontmatter")

    # Normalize some common fields if needed
    if "tags" in metadata and isinstance(metadata["tags"], str):
        metadata["tags"] = [t.strip() for t in metadata["tags"].split(",")]
        
    return {
        "metadata": metadata,
        "content": markdown_content,
        "frontmatter_raw": frontmatter_raw,
        "frontmatter_error": frontmatter_error,
    }

def normalize_category(category_name: str, aliases: list[CategoryAlias]) -> str:
    """Normalize category name via alias mapping."""
    # In-memory match for MVP
    norm_name = category_name.lower().strip()
    
    for alias in aliases:
        if alias.alias.lower() == norm_name:
            # We need the actual category slug?
            # CategoryAlias model has category_id. We might need a dict map here.
            # For simplicity, returning the resolved ID or slug requires lookup context.
            pass
            
    return norm_name # Return as-is if no match
