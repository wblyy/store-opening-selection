# store-opening-selection

**Claude Code skill for retail store opening pre-sale SKU intelligence.**

Find the right products for your store's grand opening by combining multi-channel demand
research, wholesale cost validation, and a battle-tested product-market fit framework.

## Core Framework

Every recommended SKU fits one of two types:

> **Type A**: 大家已认的商品 + 价格跌破心理预期
> Consumer has seen it at 盒马/山姆/JD. Your price is "impossible."
> Customer tells friends: *"你猜我在那家新店买了什么？M5 和牛，才 69 块。"*

> **Type B**: 大家不认识的商品 + 价格公道 + 体验惊艳
> No price anchor. First experience = new reference point.
> Customer tells friends: *"不知道为什么叫板腱，但是真的好吃，而且才 60 块。"*

A strong opening lineup needs both. Type A drives pre-sale virality. Type B creates repeat customers.

## What This Skill Does

1. **Clarifies scope** — store type, category, opening goal, constraints
2. **Validates platform access** — checks cookie freshness for 9 key platforms
3. **Runs parallel research** across 15 channels:
   - Social demand: Xiaohongshu, Douyin, Weibo
   - Expert demand: Zhihu, Bilibili
   - Supply data: Taobao (suggest API), JD, Xianyu
   - Market intelligence: Exa, Web, WeChat articles
4. **Identifies 8-12 SKU candidates** with specific part/grade/spec
5. **Classifies each** as Type A or Type B
6. **Scores on 6 dimensions**: demand strength, viral hook, price punch, supply reliability, margin, seasonality
7. **Validates costs** against ≥2 wholesale sources per SKU
8. **Outputs** Markdown report + interactive D3 dashboard

## Installation

Copy the skill directory to your Claude Code skills folder:

```bash
cp -r store-opening-selection/ ~/.claude/skills/
```

Or install directly:

```bash
git clone https://github.com/wblyy/store-opening-selection ~/.claude/skills/store-opening-selection
```

## Usage

Trigger the skill by saying:

- "开业选品" / "预售爆品"
- "开业前预售选什么好"
- "store-opening-selection"
- "开业SKU选品分析"

Or invoke explicitly: `use store-opening-selection skill`

## Files

```
store-opening-selection/
├── SKILL.md                          # Main skill instructions
└── references/
    ├── opening-sku-framework.md      # 已认/未认 framework detail + selection criteria
    ├── cost-validation.md            # Wholesale cost research methodology + pitfalls
    └── channel-coverage.md           # 15-channel coverage map + parallel execution template
```

## Origin

Distilled from session `888d56ee` (四月开业牛排选品), a real wagyu beef SKU selection
analysis for a tier-1 city hard discount supermarket's April 2026 opening. The session
involved multi-agent parallel research across 12 channels, wholesale cost validation
with 3x cost correction on one SKU, and final recommendations across 6 Type A/B products.

Key lesson from that session: **single-source wholesale costs are unreliable**. The wagyu
M5 上脑 cost estimate was off by 3x from a single listing. Always cross-validate.

## Related Skills

- [`aiselected`](https://github.com/wblyy/aiselected) — general retail product selection intelligence (this skill builds on it)
- `d3-visualization` — generates the interactive dashboard output
- `demand-research-scraper` — multi-platform data collection infrastructure

## License

MIT
