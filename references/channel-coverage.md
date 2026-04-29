# Channel Coverage Map: 15-Platform Research Guide

From session `888d56ee`. Validated 2026-03-14. Check freshness before each use.

## Priority Tier 1 — Must Have (Results Degrade Significantly Without)

| Channel | Purpose | Access Method | Status Notes |
|---------|---------|--------------|--------------|
| 小红书 | Consumer demand signals, trend detection, brand discovery language | MCP + Cookie injection | Cookie expires ~30 days. Check `~/.claude/browser-sessions/xiaohongshu.json` |
| 知乎 | Deep purchase decision questions, quality vs. price debates | Cookie + browser | High-quality for premium categories. Check `~/.claude/browser-sessions/zhihu.json` |
| 淘宝/天猫 | Supply-side sales rankings + demand via suggest API | Suggest API (no cookie) + browser | Suggest API is public, always works |
| 京东 | Supply-side cross-validation, JD-verified product specs | Browser + optional cookie | Self-operated (JD) products = highest quality baseline |

## Priority Tier 2 — High Value When Available

| Channel | Purpose | Access Method | Status Notes |
|---------|---------|--------------|--------------|
| 抖音 | Social commerce trends, live streaming product mentions | agent-reach built-in | May need VPN/CN server for some content |
| 微博 | Hot topics, KOL discussions | agent-reach built-in | Low signal for premium/B2C categories — skip if search returns <50 relevant posts |
| 闲鱼/Goofish | Secondary market flow (validates if product has post-purchase demand) | Cookie + browser | Check `~/.claude/browser-sessions/goofish.json` |
| Exa 全网搜索 | English-language market data, international reports | mcporter MCP | Best for import categories: wagyu, wine, premium dairy |
| B站 | Product review/unboxing videos, enthusiast communities | yt-dlp (metadata only) | Good for electronics, food products with visual quality signals |

## Priority Tier 3 — Supplement When Relevant

| Channel | Purpose | Access Method | Notes |
|---------|---------|--------------|-------|
| 任意网页 (Jina Reader) | Any specific article/report | WebFetch via Jina proxy | Use for industry reports, brand websites |
| Twitter/X | International consumer sentiment | xreach-cli + Cookie | Requires xreach-cli installed; useful for imported goods |
| Reddit | International discussion (e.g., wagyu r/steak, r/mealprep) | PullPush API | Best for imported products with global recognition |
| 微信公众号 | Industry analysis, supply chain reporting | wechat-article-reader skill | Search via web; article extraction via skill |
| YouTube | Video reviews for imported/premium products | yt-dlp | Metadata fetch only in most cases |
| 小宇宙播客 | Consumer lifestyle trends | Groq Whisper transcription | Requires Groq Whisper setup; high effort for incremental gain |

## Channels to Skip

| Channel | Why Skip |
|---------|---------|
| V2EX | Tech-focused community; minimal relevant food/retail discussion |
| RSS | Only useful if specific retailer/supplier feeds are subscribed |
| LinkedIn | B2B supply chain info usually better via Exa search |
| GitHub | Not applicable to retail product selection |

---

## Parallel Execution Template

For efficient multi-channel research, split into 4 parallel streams:

**Stream A — Social demand** (Xiaohongshu + Douyin + Weibo):
```
Search [{keyword}] + "推荐"/"避坑"/"多少钱"/"哪里买"
Target: posts with >1000 likes, identify pain points and wants
```

**Stream B — Expert demand** (Zhihu + B站 + YouTube):
```
Search questions framed as "哪个好"/"怎么选"/"值得买吗"
Target: answers with >500 upvotes, decision criteria
```

**Stream C — Supply data** (Taobao API + JD + Xianyu):
```
Taobao suggest API → keyword signal
JD search → top 15 products by sales + reviews
Xianyu → secondary market volume (optional)
```

**Stream D — Market intelligence** (Exa + Web + Weibo hot search):
```
Exa: "{keyword} China market 2024 2025 import"
Web: "{keyword} 价格 走势 供应商"
Weibo hot search: check if category has viral presence
```

---

## Cookie Freshness Check

Before starting research, verify cookie files exist and are recent:

```bash
ls -la ~/.claude/browser-sessions/
# Check modification dates for: xiaohongshu.json, zhihu.json, taobao.json, jd.json, goofish.json
```

If a cookie file is >30 days old, it's likely expired. Test before running research:

```bash
# Quick Zhihu test
python3 ~/.claude/skills/aiselected/scripts/zhihu_demand.py \
  --keyword "测试" --cookie-file ~/.claude/browser-sessions/zhihu.json --limit 3
```

If cookies fail, the aiselected skill's `references/platform-access.md` has refresh procedures.

---

## Actual Coverage from Wagyu Case (2026-03-14)

For reference — what was achievable with typical cookie state:

| Channel | Result | Notes |
|---------|--------|-------|
| 淘宝 suggest API | 12 keyword expansions | Always works |
| 小红书 | 449 notes analyzed | Cookie active |
| 知乎 | 158 demand signals | Cookie active |
| JD | Top 15 products + prices | Public access |
| 微博 | 0 useful signals | Not a wagyu-discussion platform |
| 闲鱼 | Not attempted | Optional for this category |
| Exa | Market size data, import stats | Works without cookie |
| 任意网页 | Industry articles via Jina | Works without cookie |
| 抖音 | Partial (no dedicated cookie) | Browser public search only |
| B站 | Not attempted | Low priority for this category |
| Twitter/X, Reddit, YouTube | Not attempted | No tooling installed |
| 微信公众号 | Not attempted | Low ROI for wagyu SKU selection |
| 小宇宙, V2EX, LinkedIn, RSS | Skipped | Not relevant |

**12/15 channels usable → sufficient for confident SKU recommendations**
