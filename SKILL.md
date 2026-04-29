---
name: store-opening-selection
description: >
  Pre-sale SKU selection intelligence for retail store openings. Identify the best
  "explosive products" (爆品) for store opening pre-sale campaigns by combining
  multi-channel market research with the "已认/未认" (Recognized vs. Undiscovered)
  product framework. Outputs a ranked SKU list with cost validation, margin analysis,
  and visual dashboard.

  Core framework: 爆品 = ("大家已认的商品" + 价格跌破心理预期) OR ("大家不认识的商品" + 价格公道 + 体验惊艳)

  Use when:
  (1) User says "开业选品"/"预售爆品"/"开业前预售"/"开业SKU"
  (2) User asks what products to feature for a store grand opening
  (3) User mentions "引流款"/"传播款"/"调性款" in a store opening context
  (4) User wants to validate product-price fit for a discount retail opening
  (5) User says "store-opening-selection" or references this skill by name
upstream: https://github.com/wblyy/store-opening-selection
---

# Store Opening Selection: Pre-Sale SKU Intelligence

Find the right products for store opening pre-sales by combining multi-channel demand signals,
wholesale cost validation, and the **Recognized vs. Undiscovered** product-market fit framework.

Core question: **Which specific SKUs will drive traffic, build brand image, and spread socially
during a store opening — while actually making margin at the discount price?**

## Core Framework: 爆品两类

Derived from session `888d56ee` (四月开业牛排选品). Every recommended SKU must fit one of:

### Type A: 大家已认的商品 + 价格跌破心理预期
- Consumer has seen this product at 盒马/山姆/京东 and has a price anchor
- The weapon: same quality, price at an "impossible" position
- Success signal: customer says "这价格怎么可能"
- Examples: M5 wagyu ribeye, branded imported fruit, name-brand protein powder

### Type B: 大家不认识的商品 + 价格公道 + 体验惊艳
- Consumer has no price anchor for this product — no comparison possible
- The weapon: low cognitive barrier + high experience + fair pricing = "discovery moment"
- Success signal: customer says "没听过这个，但是好好吃啊"
- Examples: wagyu flat iron steak (板腱), obscure Japanese snacks, regional specialty foods

**Which type to lead with**: Type A for traffic and virality (known + shocking price).
Type B for margin and differentiation (unknown + genuine delight). Opening lineup needs both.

See [references/opening-sku-framework.md](references/opening-sku-framework.md) for full framework.

---

## Workflow

### Step 0: Clarify Scope

Ask the user (use AskUserQuestion if not already provided):
1. **Category** — what product category? Be specific (e.g., "进口牛肉" not "生鲜")
2. **Store type** — hard discount / community fresh / convenience? City tier?
3. **Opening goal** — traffic / brand image / social spread? (can be multiple)
4. **Constraints** — cold chain, shelf life, supplier availability, price ceiling?
5. **Timeline** — weeks until opening? Pre-sale window?

Build 3-5 core search keywords including synonyms and sub-categories.

### Step 1: Validate Platform Access

Check available cookie sessions:

```bash
ls ~/.claude/browser-sessions/
```

Priority platforms (results degrade significantly without these):
- **Xiaohongshu** — demand + trend signals (consumer discovery language)
- **Zhihu** — deep purchase decision questions
- **Taobao** — supply-side sales rankings
- **JD** — supply-side cross-validation

See [references/channel-coverage.md](references/channel-coverage.md) for full 15-channel map.

### Step 2: Demand Research (Parallelize)

Goal: Is there active consumer demand? What specific products/features are people seeking?

Run 4 parallel research streams:

**Stream 1 — Social demand** (Xiaohongshu + Douyin):
- Search `{keyword}` + "推荐" / "避坑" / "多少钱" / "哪里买"
- Target: notes with >1000 likes, identify recurring asks and pain points
- Extract: specific product mentions, price sensitivity signals, gifting vs. self-use split

**Stream 2 — Expert demand** (Zhihu):
- Search questions framed as "哪个好"/"怎么选"/"值得买吗"
- Target: questions with >100 followers and answers with >500 upvotes
- Extract: decision criteria, trust signals, quality vs. price tradeoffs

**Stream 3 — Mass demand** (Weibo + web search):
- Check if category has hot search presence
- Search `{keyword} 推荐 {year}` on Baidu
- Note: some B2C categories (premium meats, luxury snacks) have near-zero Weibo signal — skip if dry

**Stream 4 — Supply demand signals** (Taobao suggest API):
```bash
# No cookie needed — public suggest API
curl "https://suggest.taobao.com/sug?code=utf-8&q={keyword}" | python3 -m json.tool
```
Taobao autocomplete = what consumers actually type = highest-quality demand signal.

Score demand strength using 5 dimensions (each 1-5):
1. Search volume & trend
2. Recency (signals from last 90 days)
3. Purchase intent (not just curiosity)
4. Pain point clarity (specific asks, not vague interest)
5. Price discussion (signals price sensitivity)

### Step 3: Supply Research (Parallelize)

Goal: What's already selling well? Price bands, market leaders, quality gaps?

**Taobao/JD top products**: Identify top 10-15 SKUs by sales, note price ranges, brands, specs.
Focus on products with >1000 monthly sales + review volume indicating real demand.

**Wholesale cost research** (CRITICAL — do not skip):
Run via browser automation on 1-2 wholesale platforms:
- 惠农网 (`huinong.com`) — agricultural/fresh produce B2B
- 1688 — general wholesale (may hit captcha; try browser automation)
- 农贸易家, 果夏生活 — for fresh/imported products

**Cross-validate costs across at least 2 independent sources.**
Single-source cost estimates lead to wrong margin calculations.
See [references/cost-validation.md](references/cost-validation.md) for methodology and common pitfalls.

**Competitive retail scan**: Check if target category has presence at:
- 山姆, 盒马 — premium anchor pricing
- 叮咚买菜, 朴朴 — community fresh pricing
- 近邻宝, ALDI China — hard discount comparable

### Step 4: SKU Candidate Identification

Merge demand signals + supply data to identify 8-12 SKU candidates.
For each candidate, record:
- Specific product (part/grade/spec, e.g., "M5 板腱 200g" not just "wagyu")
- Retail price at competitors
- Estimated wholesale cost (with source)
- Consumer language for this product (how people search/describe it)
- Type A or Type B classification

### Step 5: Classify by Framework

Apply the 已认/未认 framework to each candidate:

**For Type A candidates**, verify:
- Is there a clear price anchor? (consumer has seen it elsewhere)
- How much would our price need to undercut to create the "impossible" reaction? (usually >40%)
- Is the quality verifiable without expertise? (wagyu marbling grade is visible)

**For Type B candidates**, verify:
- Is it genuinely unknown to target consumers? (not just unfamiliar to the researcher)
- Can the experience surprise someone who has no expectations? (key: zero anchoring = pure delight)
- Is the name/appearance enticing without explanation? (can't require a lecture to sell)

Eliminate candidates that fit neither type cleanly — those are middle-ground products
that neither shock nor delight. Hard discount has no room for "meh."

### Step 6: Score and Rank (6 Dimensions)

Score each candidate on 6 dimensions (each 1-5, weighted):

| Dimension | Weight | What it measures |
|-----------|--------|-----------------|
| 需求强度 | 25% | Search volume, trend direction, platform signal depth |
| 价格击穿感 (Type A) / 体验惊艳感 (Type B) | 25% | How powerful is the core value proposition? |
| 传播潜力 | 20% | One sentence: can a customer forward this to 3 friends? |
| 供给可靠性 | 15% | Supplier availability, cold chain, lead time risk |
| 毛利空间 | 10% | (Retail price - wholesale cost) / retail price |
| 应季适配 | 5% | Does the opening month/season boost or hurt this product? |

Sort by weighted total. Final recommendation: top 4-6 SKUs.
Aim for 2-3 Type A + 2-3 Type B in the final set.

### Step 7: Cost Validation Pass

Before finalizing, validate costs for the top 6 candidates:
- At least 2 independent wholesale sources per SKU
- Flag if the two sources diverge >30% (investigate before proceeding)
- Recalculate margin with corrected costs
- Drop any SKU where validated margin < 25%

**Common cost traps** (learned from wagyu case):
1. Cheap listings on wholesale platforms ≠ available at that price. Call to verify.
2. "和牛肥牛片" at suspiciously low prices are usually non-wagyu blended product. Grade ≠ claim.
3. Single-source costs multiplied by assumed ratios (e.g., "JD retail × 0.3 = wholesale") fail regularly.
4. Import product costs fluctuate with AUD/USD and shipping. Get fresh quotes.

### Step 8: Output Report

Generate two deliverables:

**1. Markdown Report** (`outputs/store-opening-selection-{category}-{date}.md`):
- Executive summary (3 sentences: context, recommendation, confidence)
- Final SKU table (6 columns: SKU, type, suggested price, anchor price, wholesale cost, margin)
- Per-SKU narrative: why this product, what the transmission hook is
- Data coverage table (which channels contributed what)
- Cost validation appendix (sources, dates, reliability ratings)

**2. D3 Dashboard** (`outputs/store-opening-dashboard-{date}.html`):
Call `/d3-visualization` skill. Dashboard should include:
- SKU ranking bar chart (weighted scores, color-coded by A/B type)
- Price undercutting comparison (competitor price vs. our price)
- Margin waterfall (wholesale cost + margin stack)
- Demand radar (5-dimension demand strength)
- 6-dimension scoring heatmap
- Platform coverage visualization (channels used, signal counts)

See [references/opening-sku-framework.md](references/opening-sku-framework.md) for full report template.

---

## Quick Reference: What Separates a Good Opening SKU

From the wagyu case, ranked by importance:

1. **One-sentence virality**: "硬折扣超市卖 M5 和牛，69 块钱一块" — can be forwarded as-is
2. **Visible quality signal**: customer can verify quality without expertise (marbling, color, weight)
3. **Price needs no explanation**: the gap between our price and anchor price is self-evident
4. **First-timer friendly**: no cooking expertise required to have a good experience
5. **Second-purchase trigger**: good enough to come back, not good enough to feel "done"

## When to Stop

If demand signals are weak across all platforms (<10 relevant signals per channel), pause.
Either the category is wrong for the target consumer, or the timing is off. Report the gap
before recommending products — do not fill weak data with educated guesses.

See MEMORY rule: "没有数据就说'数据待补全'，不要用话术掩饰缺失。"
