# Cost Validation Methodology

Hard-learned from wagyu case (session `888d56ee`). Read this before finalizing any margin estimate.

## Why Single-Source Costs Fail

In the wagyu analysis, the initial cost estimate for M5 上脑 was ¥7.5/100g (from a single
惠农网 listing). Multi-source validation revealed the actual range was ¥12.5-14.4/100g —
a **3x error** that would have made the recommended ¥49.9/300g pricing a loss-leader rather
than a 40% margin product.

Single-source cost traps, in order of frequency:

1. **Stale listings** — wholesale platforms don't always update prices. A posting from 6 months
   ago may reflect a very different market. Always check the listing date.

2. **Grade substitution** — "和牛肥牛片" at suspiciously low prices (e.g., ¥3-4/100g) is
   almost always a blended or non-wagyu product. Genuine M5+ product has a cost floor.
   Rule of thumb: M5 wagyu parts should cost ≥ ¥8/100g at wholesale. Below that = investigate.

3. **Ratio extrapolation errors** — "JD retail × 0.3 = wholesale" is an approximation,
   not a fact. Batch-retail ratio varies by category, supplier, and volume.
   For fresh/imported products, the ratio is often 0.4-0.6x (thinner than expected).

4. **Currency/shipping volatility** — imported products priced in AUD, USD, or EUR
   can shift 10-20% over a quarter. Cost estimates from 3+ months ago need refreshing.

5. **Volume minimums** — a supplier may quote ¥X/kg for a minimum order of 200kg.
   Your first order may be 20kg. The actual price will be higher.

---

## Validation Protocol

### Step 1: Identify 3+ independent cost sources

For each SKU candidate, gather costs from at least **3 independent sources**:

| Source type | Platform examples | Reliability |
|-------------|------------------|-------------|
| B2B wholesale platform | 惠农网, 农贸易家, 果夏生活 | Medium (prices may be stale) |
| B2B marketplace (buyer-side) | 1688 | Medium-High (many sellers, price range visible) |
| Wholesale market data | 华南冷链, MarbleMore B2B | High (if recent) |
| Competitor retail reverse | 盒马, 山姆, JD (×0.4-0.55) | Low-Medium (ratio varies) |
| Direct supplier inquiry | Phone/WeChat to supplier | High (actual quote, recent) |

### Step 2: Spot divergence

If two sources diverge by **>30%**, investigate before proceeding:
- Which source is more recent?
- Which source specifies grade/spec more clearly?
- Could one source be a different product (e.g., different cut, different grade)?

### Step 3: Record the range, not a point estimate

Never write "cost = ¥X/100g". Write "cost range: ¥X-Y/100g (sources: A + B + C)".
Calculate margin using the **upper bound** of the cost range for conservative planning.

### Step 4: Flag speculative costs clearly

If you can't find 2+ independent sources for a SKU, flag it explicitly:
```
⚠️ COST UNVERIFIED: Only 1 source available. Margin estimate is provisional.
Validate before finalizing pricing.
```

Never present a single-source cost as confirmed.

---

## Wholesale Platform Access Notes

### 惠农网 (huinong.com)
- Good for: fresh produce, imported meat, premium ingredients
- Access: public browse without login for listings; call/WeChat for actual quotes
- Pitfall: listings may be months old. Check post date.

### 1688
- Good for: general merchandise, packaged goods, non-fresh products
- Access: browser automation often hits captcha (slider verification) on search
- Workaround: use direct category URL navigation rather than search
- Cookie status: login cookie often expires. `__cn_logon__=false` = guest mode, no real prices

### 农贸易家 / 果夏生活
- Good for: fresh produce, fruits, specialty foods
- Access: public browse
- Note: smaller platform, fewer listings but prices tend to be more current

### MarbleMore (marblemore.cn)
- Good for: premium imported beef, specifically wagyu grades
- Access: public browse for B2C; contact for B2B wholesale
- High reliability for wagyu specifically

---

## Margin Calculation Template

```
SKU: [name]
Suggested retail price: ¥X
Wholesale cost (range): ¥Y - ¥Z (sources: [list])
Conservative margin: ([X - Z] / X) × 100 = %
Optimistic margin: ([X - Y] / X) × 100 = %
Decision: proceed if conservative margin ≥ 25%
```

**Minimum viable margins for opening lineup**:
- Traffic/引流款: ≥ 20% (you're paying for foot traffic with margin)
- Standard products: ≥ 35%
- Differentiation products (Type B): ≥ 50% (this is where you make money)

---

## The "Honest Cost" Rule

From MEMORY: "没有数据就说'数据待补全'，不要用话术掩饰缺失"

If wholesale cost is genuinely unknown:
1. Note it explicitly in the report
2. Provide a range based on comparable products with sources
3. Recommend the SKU conditionally: "promising IF wholesale cost is ≤ ¥X — validate before committing"
4. Never present a speculative number as a fact

A gap in cost data caught before the opening lineup is finalized costs nothing.
A gap discovered after you've committed to pricing and marketing can cost everything.
