#!/usr/bin/env python3
"""
SKU scorer for store opening pre-sale selection.
Applies the 6-dimension scoring framework from store-opening-selection skill.

Reads SKU candidates from a JSON file or stdin, scores each on 6 dimensions,
outputs ranked results with type classification (A/B) and margin analysis.

Usage:
    python3 sku_scorer.py --input skus.json
    cat skus.json | python3 sku_scorer.py --input -
    python3 sku_scorer.py --demo  # run with built-in wagyu example

Input JSON format:
    {
      "category": "澳洲和牛",
      "store_type": "硬折扣超市",
      "skus": [
        {
          "name": "M5 眼肉牛排 200g",
          "type": "A",
          "our_price": 69.9,
          "anchor_price": 138,
          "anchor_source": "盒马",
          "wholesale_cost_low": 28,
          "wholesale_cost_high": 32,
          "demand_score": 4,
          "viral_score": 5,
          "supply_score": 4,
          "season_score": 3,
          "notes": "消费者见过盒马卖138，69块击穿预期"
        }
      ]
    }

Output: JSON with scores, rankings, and type A/B classification.
"""
import argparse
import json
import sys

# ─────────────────────────────────────────────
# Scoring weights (must sum to 1.0)
# ─────────────────────────────────────────────

DIMENSION_WEIGHTS = {
    "demand_score": 0.25,       # Search volume, trend direction, platform signal depth
    "punch_score": 0.25,        # Price punch (Type A) or experience wow (Type B)
    "viral_score": 0.20,        # Virality: can customer forward this in one sentence?
    "supply_score": 0.15,       # Supply reliability: availability, cold chain, lead time
    "margin_score": 0.10,       # (Retail - wholesale cost) / retail
    "season_score": 0.05,       # Seasonal fit for opening month
}

assert abs(sum(DIMENSION_WEIGHTS.values()) - 1.0) < 0.001, "Weights must sum to 1.0"

# Minimum viable margins by product role
MIN_MARGINS = {
    "traffic": 0.20,            # 引流款 — acceptable lower margin for foot traffic
    "standard": 0.35,           # Standard products
    "differentiation": 0.50,    # Type B differentiation products
}


def compute_margin_score(sku):
    """
    Score margin on 1-5 scale.
    Uses conservative estimate (wholesale_cost_high / our_price).
    """
    our_price = sku.get("our_price", 0)
    cost_high = sku.get("wholesale_cost_high", 0)
    cost_low = sku.get("wholesale_cost_low", 0)

    if our_price <= 0:
        return 1, None, None, "no price data"

    if cost_high <= 0:
        return 2, None, None, "cost unverified — provisional score 2/5"

    margin_conservative = (our_price - cost_high) / our_price
    margin_optimistic = (our_price - cost_low) / our_price if cost_low > 0 else None

    # Score: 5 = margin ≥ 60%, 4 = 45-60%, 3 = 30-45%, 2 = 15-30%, 1 = <15%
    if margin_conservative >= 0.60:
        score = 5
    elif margin_conservative >= 0.45:
        score = 4
    elif margin_conservative >= 0.30:
        score = 3
    elif margin_conservative >= 0.15:
        score = 2
    else:
        score = 1

    return score, round(margin_conservative, 3), (
        round(margin_optimistic, 3) if margin_optimistic else None
    ), "ok"


def compute_punch_score(sku):
    """
    Type A: Price punch = how shocking is the discount?
    Type B: Experience wow = caller must provide wow_score directly.
    """
    sku_type = sku.get("type", "A")

    if sku_type == "B":
        # Type B: experience wow score (caller provides 1-5, default 3)
        return sku.get("wow_score", 3), "Type B: experience wow score"

    # Type A: calculate from price cut
    our_price = sku.get("our_price", 0)
    anchor_price = sku.get("anchor_price", 0)

    if anchor_price <= 0 or our_price <= 0:
        return 2, "no anchor price"

    discount = (anchor_price - our_price) / anchor_price

    # Score: 5 = >55% off, 4 = 40-55%, 3 = 25-40%, 2 = 10-25%, 1 = <10%
    if discount >= 0.55:
        score = 5
    elif discount >= 0.40:
        score = 4
    elif discount >= 0.25:
        score = 3
    elif discount >= 0.10:
        score = 2
    else:
        score = 1

    anchor_source = sku.get("anchor_source", "competitor")
    return score, f"Type A: {round(discount*100)}% off vs {anchor_source} (¥{anchor_price}→¥{our_price})"


def score_sku(sku):
    """Score a single SKU. Returns enriched SKU dict with scores and ranking metadata."""
    result = dict(sku)

    # Compute derived scores
    margin_score, margin_conservative, margin_optimistic, margin_note = compute_margin_score(sku)
    punch_score, punch_note = compute_punch_score(sku)

    result["scores"] = {
        "demand_score": sku.get("demand_score", 3),
        "punch_score": punch_score,
        "viral_score": sku.get("viral_score", 3),
        "supply_score": sku.get("supply_score", 3),
        "margin_score": margin_score,
        "season_score": sku.get("season_score", 3),
    }

    # Weighted total (1-5 scale)
    total = sum(
        result["scores"][dim] * weight
        for dim, weight in DIMENSION_WEIGHTS.items()
    )
    result["weighted_total"] = round(total, 3)

    # Margin analysis
    result["margin_analysis"] = {
        "conservative": margin_conservative,
        "optimistic": margin_optimistic,
        "score": margin_score,
        "note": margin_note,
    }
    if margin_conservative is not None:
        sku_type = sku.get("type", "A")
        min_margin = MIN_MARGINS["traffic"] if sku_type == "A" else MIN_MARGINS["differentiation"]
        result["margin_analysis"]["viable"] = margin_conservative >= min_margin
        if not result["margin_analysis"]["viable"]:
            result["margin_analysis"]["warning"] = (
                f"Conservative margin {round(margin_conservative*100)}% "
                f"below minimum {round(min_margin*100)}% for {'Type A traffic' if sku_type == 'A' else 'Type B'} product"
            )

    result["punch_analysis"] = {"score": punch_score, "note": punch_note}

    # Type validation
    sku_type = sku.get("type")
    if sku_type not in ("A", "B"):
        result["type_warning"] = "type must be 'A' or 'B' — defaulting to A"
        result["type"] = "A"

    # Viral hook check
    if not sku.get("viral_hook"):
        result["viral_hook_missing"] = (
            "Add 'viral_hook': one sentence a customer would say to a friend. "
            "Missing viral hook is a red flag."
        )

    return result


def rank_skus(skus_data):
    """Score and rank all SKUs. Returns enriched data with rankings."""
    skus = skus_data.get("skus", [])
    if not skus:
        return {"error": "no skus in input", "input": skus_data}

    scored = [score_sku(sku) for sku in skus]
    scored.sort(key=lambda x: x["weighted_total"], reverse=True)

    for i, sku in enumerate(scored):
        sku["rank"] = i + 1

    # Separate by type
    type_a = [s for s in scored if s.get("type") == "A"]
    type_b = [s for s in scored if s.get("type") == "B"]

    # Portfolio check
    warnings = []
    if len(type_a) == 0:
        warnings.append("No Type A (Recognized + Price Shock) products. Opening lineup needs at least 1 for virality.")
    if len(type_b) == 0:
        warnings.append("No Type B (Unknown + Experience Wow) products. Opening lineup needs at least 1 for repeat customers.")
    if len(scored) < 4:
        warnings.append("Fewer than 4 total SKUs. Recommended: 4-6 for a balanced opening lineup.")

    # Margin failures
    margin_failures = [
        s["name"] for s in scored
        if s.get("margin_analysis", {}).get("viable") is False
    ]
    if margin_failures:
        warnings.append(f"Margin below minimum for: {', '.join(margin_failures)} — validate costs before committing.")

    result = dict(skus_data)
    result["scored_skus"] = scored
    result["portfolio_summary"] = {
        "total": len(scored),
        "type_a_count": len(type_a),
        "type_b_count": len(type_b),
        "top_pick": scored[0]["name"] if scored else None,
        "warnings": warnings,
    }

    return result


# ─────────────────────────────────────────────
# Demo data (wagyu case from session 888d56ee)
# ─────────────────────────────────────────────

DEMO_INPUT = {
    "category": "澳洲和牛",
    "store_type": "硬折扣超市",
    "opening_month": "April",
    "skus": [
        {
            "name": "M5 眼肉牛排 200g",
            "type": "A",
            "our_price": 69.9,
            "anchor_price": 138,
            "anchor_source": "盒马",
            "wholesale_cost_low": 28,
            "wholesale_cost_high": 32,
            "demand_score": 5,
            "viral_score": 5,
            "supply_score": 4,
            "season_score": 3,
            "viral_hook": "盒马卖138，这家才69，还是M5的",
        },
        {
            "name": "M5 板腱牛排 200g",
            "type": "B",
            "our_price": 59.9,
            "anchor_price": 0,
            "wholesale_cost_low": 18,
            "wholesale_cost_high": 22,
            "demand_score": 3,
            "wow_score": 5,
            "viral_score": 3,
            "supply_score": 5,
            "season_score": 4,
            "viral_hook": "叫板腱，比眼肉还嫩，才60块",
        },
        {
            "name": "M5 肥牛火锅片 300g",
            "type": "A",
            "our_price": 59.9,
            "anchor_price": 89,
            "anchor_source": "山姆",
            "wholesale_cost_low": 38,
            "wholesale_cost_high": 48,
            "demand_score": 5,
            "viral_score": 4,
            "supply_score": 3,
            "season_score": 2,
            "viral_hook": "山姆89的火锅片，这家59，M5的",
            "notes": "Spring is off-season for hot pot. Cost range wide — validate before commit.",
        },
        {
            "name": "M7 西冷牛排 200g",
            "type": "A",
            "our_price": 99.9,
            "anchor_price": 188,
            "anchor_source": "盒马",
            "wholesale_cost_low": 52,
            "wholesale_cost_high": 62,
            "demand_score": 4,
            "viral_score": 4,
            "supply_score": 3,
            "season_score": 3,
            "viral_hook": "M7西冷，盒马卖188，开业价99",
        },
        {
            "name": "M5 上脑烤肉片 200g",
            "type": "B",
            "our_price": 39.9,
            "anchor_price": 0,
            "wholesale_cost_low": 25,
            "wholesale_cost_high": 30,
            "demand_score": 4,
            "wow_score": 4,
            "viral_score": 3,
            "supply_score": 4,
            "season_score": 5,
            "viral_hook": "烤肉片，油花超均匀，39块，和牛的",
        },
    ],
}


def main():
    parser = argparse.ArgumentParser(
        description="6-dimension SKU scorer for store opening pre-sale selection"
    )
    parser.add_argument(
        "--input", default="-",
        help="JSON file path or '-' for stdin (default: stdin)"
    )
    parser.add_argument(
        "--demo", action="store_true",
        help="Run with built-in wagyu demo data (ignores --input)"
    )
    parser.add_argument(
        "--top", type=int, default=0,
        help="Show only top N SKUs (default: all)"
    )
    args = parser.parse_args()

    if args.demo:
        data = DEMO_INPUT
    elif args.input == "-":
        data = json.load(sys.stdin)
    else:
        with open(args.input) as f:
            data = json.load(f)

    result = rank_skus(data)

    if args.top > 0 and "scored_skus" in result:
        result["scored_skus"] = result["scored_skus"][: args.top]

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
