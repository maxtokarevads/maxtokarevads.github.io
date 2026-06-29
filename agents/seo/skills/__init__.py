from .prompt         import build_seo_prompt
from .aeo            import build_aeo_prompt
from .technical      import build_technical_prompt
from .content        import build_content_prompt
from .local          import build_local_prompt
from .schema         import build_schema_prompt
from .backlinks      import build_backlinks_prompt
from .cluster        import build_cluster_prompt
from .sxo            import build_sxo_prompt
from .canon          import build_seo_audit_prompt
from .write          import (
    build_article_prompt,
    build_brief_prompt,
    build_meta_prompt,
    build_rewrite_prompt,
)

SUPPORTED_MODES = [
    "seo",        # general SEO strategy (default)
    "aeo",        # AI/answer engine optimization
    "technical",  # 9-category technical audit + health score
    "content",    # E-E-A-T content quality assessment
    "local",      # local SEO: GBP, NAP, citations, reviews
    "schema",     # schema markup audit + JSON-LD generation
    "backlinks",  # backlink audit + link building strategy
    "cluster",    # topical cluster + keyword architecture
    "sxo",        # search experience optimization (SERP-backward)
    "audit",      # full Canon audit (30 rules, P0/P1/P2)
    "drift",      # SEO drift monitoring vs baseline
    # ── Content writing sub-agent ──
    "article",    # write full SEO article (title, H2/H3, body, meta, FAQ)
    "brief",      # content brief for a copywriter
    "meta",       # write / optimise meta titles + descriptions
    "rewrite",    # rewrite existing content for E-E-A-T + keywords
]

__all__ = [
    "build_seo_prompt", "build_aeo_prompt", "build_technical_prompt",
    "build_content_prompt", "build_local_prompt", "build_schema_prompt",
    "build_backlinks_prompt", "build_cluster_prompt", "build_sxo_prompt",
    "build_seo_audit_prompt",
    "build_article_prompt", "build_brief_prompt",
    "build_meta_prompt", "build_rewrite_prompt",
    "SUPPORTED_MODES",
]
