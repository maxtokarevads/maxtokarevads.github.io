"""
Human-readable labels for Obsidian vault notes.
Kept outside agents/ so the no-Cyrillic test stays green.
"""

ADS_MODE_LABELS: dict = {
    "plan":        "Планування кампанії",
    "analyze":     "Аналіз метрик",
    "copy":        "Тексти реклами",
    "retargeting": "Ремаркетинг",
    "ab_test":     "A/B тест",
    "budget":      "Розподіл бюджету",
    "audit":       "Аудит",
    "research":    "Ресерч",
    "landing":     "Аудит лендингу",
    "forecast":    "Прогноз",
}

ADS_PLATFORM_LABELS: dict = {
    "google": "Google Ads",
    "meta":   "Meta Ads",
    "tiktok": "TikTok Ads",
}

SEO_MODE_LABELS: dict = {
    "seo":       "SEO Стратегія",
    "aeo":       "AEO / GEO",
    "technical": "Технічний аудит",
    "content":   "Контент / E-E-A-T",
    "local":     "Локальне SEO",
    "schema":    "Schema / JSON-LD",
    "backlinks": "Посилальний профіль",
    "cluster":   "Топічний кластер",
    "sxo":       "SXO",
    "audit":     "Canon SEO Аудит",
    "drift":     "Drift моніторинг",
    "article":   "SEO Стаття",
    "brief":     "Контент бриф",
    "meta":      "Meta теги",
    "rewrite":   "Рерайт контенту",
}

STRATEGY_MODE_LABELS: dict = {
    "general":     "Маркетингова стратегія",
    "gtm":         "Go-to-Market план",
    "positioning": "Позиціонування",
    "channel_mix": "Мікс каналів",
    "kpi":         "KPI фреймворк",
    "audit":       "Canon Strategy Аудит",
}

CREATIVE_MODE_LABELS: dict = {
    "concept":   "Концепція креативу",
    "copy":      "Тексти / Copy",
    "script":    "Відео скрипт",
    "ugc_brief": "UGC Бриф",
}

# Field labels used in vault note bodies
FIELD_PLATFORM  = "Платформа"
FIELD_MODE      = "Режим"
FIELD_PRODUCT   = "Продукт"
FIELD_GOAL      = "Ціль"
FIELD_DATE      = "Дата"
FIELD_SITE      = "Сайт"
FIELD_NICHE     = "Ніша"
FIELD_KEYWORDS  = "Ключові слова"
FIELD_HORIZON   = "Горизонт"
FIELD_TONE      = "Тон"
FIELD_FUNNEL    = "Етап воронки"
FIELD_PREV      = "Попередня"
FIELD_METRICS   = "Метрики"
