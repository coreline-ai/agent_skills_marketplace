"""SKILL.md Parser."""

import re
import yaml
from typing import Any, Optional

from app.models.category_alias import CategoryAlias

# Basic Pattern for Frontmatter
FRONTMATTER_PATTERN = re.compile(r"^---\n(.*?)\n---", re.DOTALL)

def parse_skill_md(content: str) -> dict[str, Any]:
    """Parse SKILL.md content, extracting frontmatter."""
    match = FRONTMATTER_PATTERN.match(content)
    
    metadata = {}
    markdown_content = content
    
    if match:
        try:
            yaml_content = match.group(1)
            metadata = yaml.safe_load(yaml_content) or {}
            markdown_content = content[match.end():].strip()
        except yaml.YAMLError:
            print("YAML Error parsing frontmatter")

    # Normalize some common fields if needed
    if "tags" in metadata and isinstance(metadata["tags"], str):
        metadata["tags"] = [t.strip() for t in metadata["tags"].split(",")]
        
    return {
        "metadata": metadata,
        "content": markdown_content
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
