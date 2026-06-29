# AdsAgent

Специализированный агент для платной рекламы. Поддерживает **Google Ads**, **Meta (Facebook/Instagram)** и **TikTok Ads**.

## Режимы (mode)

| mode | Описание |
|------|----------|
| `plan` | Стратегия запуска новой кампании (по умолчанию) |
| `analyze` | Диагностика метрик существующей кампании |
| `copy` | Генерация текстов / видео-скриптов объявлений |
| `retargeting` | Стратегия ремаркетинга по воронке TOFU→MOFU→BOFU |
| `ab_test` | Дизайн A/B тестов |
| `budget` | Распределение бюджета между платформами (кросс-платформенный) |

## Payload

```python
{
    "platform": "google",          # google | meta | facebook | instagram | tiktok
    "mode": "plan",                # см. таблицу выше
    "product": "SaaS CRM tool",    # описание продукта
    "budget": 3000,                # бюджет в $ в месяц
    "goal": "free trial signups",  # цель кампании
    "usp": "10x faster onboarding",# уникальное предложение
    "industry": "saas",            # saas | ecom | leadgen | app
    "funnel_stage": "tofu",        # tofu | mofu | bofu
    "audience_type": "cold",       # cold | warm | hot
    "audience": {
        "age": "25-45",
        "location": "US",
        "interest": "software, productivity"
    },
    "landing_page": "https://...", # URL лендинга
    # --- для mode: analyze ---
    "metrics": {
        "ctr": 1.8,
        "cpc": 2.4,
        "cpa": 48,
        "roas": 2.1,
        "impressions": 50000,
        "clicks": 900,
        "conversions": 62,
        "spend": 2980,
        # Google: quality_score, impression_share, lost_is_budget, lost_is_rank
        # Meta: frequency, hook_rate, video_completion_rate, relevance_score
        # TikTok: hook_rate, video_completion_rate, avg_watch_time, engagement_rate
    },
    # --- для mode: copy ---
    "keywords": ["crm", "project management"],  # Google
    "tone": "professional",
    "duration": "15 sec",          # TikTok
    # --- для mode: retargeting ---
    "has_pixel": True,
    "has_crm_list": False,
    "has_catalog": False,
    # --- для mode: ab_test ---
    "what_to_test": "bidding strategy",
    "current_performance": {"ctr": 1.2, "cpa": 55},
    # --- для mode: budget ---
    "platforms": ["google", "meta", "tiktok"],
}
```

## Лимиты платформ (актуально 2026)

### Google Ads RSA
- Заголовки: 15 × ≤30 символов
- Описания: 4 × ≤90 символов

### Meta Ads
- Primary Text: ≤125 символов
- Headline: ≤27 символов
- Description: ≤27 символов

### TikTok Ads
- Caption: ≤100 символов
- Формат видео: только 9:16 (1080×1920px)
- Звук обязателен

## Пример использования

```python
from agent import AdvertisingAnalyticsAgent

a = AdvertisingAnalyticsAgent()

# Анализ кампании Meta
result = a.run_agent("ads", {
    "platform": "meta",
    "mode": "analyze",
    "product": "SaaS CRM",
    "metrics": {
        "ctr": 0.8,
        "frequency": 5.2,
        "hook_rate": 14,
        "cpa": 72,
        "roas": 1.9,
    }
})

# Копирайтинг для Google
result = a.run_agent("ads", {
    "platform": "google",
    "mode": "copy",
    "product": "Project management SaaS",
    "usp": "Deploy in 5 minutes",
    "keywords": ["project management tool", "team collaboration"],
    "goal": "free trial signup",
})

# Распределение бюджета
result = a.run_agent("ads", {
    "mode": "budget",
    "platforms": ["google", "meta", "tiktok"],
    "budget": 10000,
    "goal": "conversions",
    "industry": "saas",
})
```
