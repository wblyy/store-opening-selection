#!/usr/bin/env python3
"""
Main orchestrator for store opening SKU selection analysis.
Coordinates the 8-step workflow from SKILL.md.

Usage:
    # Full workflow with cost validation
    python3 run_analysis.py --category "澳洲和牛" --store "硬折扣超市" --city "北京" --month April

    # Score existing SKU candidates from a JSON file
    python3 run_analysis.py --score-only --input candidates.json

    # Validate costs for a specific keyword
    python3 run_analysis.py --cost-check --keyword "澳洲和牛 M5 眼肉"

    # Run demo with wagyu example data
    python3 run_analysis.py --demo

This script is the CLI bridge between Claude Agent and the skill scripts.
Claude calls this to trigger structured data collection, then interprets
the JSON output to produce the final analysis report.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def run_script(script_name, args_list, timeout=30):
    """Run a sibling script and return parsed JSON output."""
    script_path = os.path.join(SCRIPT_DIR, script_name)
    cmd = [sys.executable, script_path] + args_list
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        if result.returncode != 0:
            return {
                "status": "script_error",
                "stderr": result.stderr[:500],
                "script": script_name,
            }
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "script": script_name}
    except json.JSONDecodeError as e:
        return {"status": "parse_error", "error": str(e), "script": script_name}
    except Exception as e:
        return {"status": "error", "error": str(e), "script": script_name}


# ─────────────────────────────────────────────
# Step 1–3: Market research (delegates to aiselected scripts)
# ─────────────────────────────────────────────

def run_market_research(keywords, cookie_dir=None):
    """
    Run multi-source market research for a category.
    Delegates to aiselected scripts for platform-specific collection.
    Returns aggregated demand signals.
    """
    cookie_dir = cookie_dir or os.path.expanduser("~/.claude/browser-sessions")
    aiselected_scripts = os.path.expanduser("~/.claude/skills/aiselected/scripts")

    results = {}
    for keyword in keywords[:3]:  # limit to 3 keywords to avoid overlong runs
        kw_results = {}

        # Taobao suggest (no cookie needed — always run)
        taobao_res = run_script(
            "wholesale_scraper.py",
            ["--keyword", keyword, "--sources", "taobao", "--limit", "5"],
        )
        kw_results["taobao_demand"] = taobao_res

        # Zhihu (if cookie available)
        zhihu_cookie = os.path.join(cookie_dir, "zhihu.json")
        if os.path.exists(zhihu_cookie) and os.path.exists(
            os.path.join(aiselected_scripts, "zhihu_demand.py")
        ):
            zhihu_res = run_script(
                os.path.join(aiselected_scripts, "zhihu_demand.py"),
                ["--keyword", keyword, "--cookie-file", zhihu_cookie, "--limit", "10"],
                timeout=20,
            )
            kw_results["zhihu"] = zhihu_res
        else:
            kw_results["zhihu"] = {
                "status": "skipped",
                "reason": "cookie not found or aiselected not installed",
            }

        results[keyword] = kw_results
        time.sleep(0.3)

    return results


# ─────────────────────────────────────────────
# Step 5–7: Cost validation + scoring
# ─────────────────────────────────────────────

def run_cost_validation(keywords):
    """Validate wholesale costs for given keywords."""
    results = {}
    for keyword in keywords:
        cost_data = run_script(
            "wholesale_scraper.py",
            ["--keyword", keyword, "--sources", "taobao,jd,huinong,1688"],
        )
        results[keyword] = cost_data
        time.sleep(0.5)
    return results


def run_sku_scoring(candidates_json):
    """Score SKU candidates using sku_scorer.py."""
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(candidates_json, f, ensure_ascii=False)
        tmp_path = f.name

    result = run_script("sku_scorer.py", ["--input", tmp_path])
    os.unlink(tmp_path)
    return result


# ─────────────────────────────────────────────
# Report generation
# ─────────────────────────────────────────────

def generate_report(analysis_data, output_path=None):
    """Generate a Markdown report from analysis results."""
    category = analysis_data.get("category", "unknown")
    store_type = analysis_data.get("store_type", "retail store")
    opening_month = analysis_data.get("opening_month", "")
    scored_skus = analysis_data.get("scored_skus", [])
    portfolio = analysis_data.get("portfolio_summary", {})
    market_research = analysis_data.get("market_research", {})
    cost_validation = analysis_data.get("cost_validation", {})

    now = datetime.now().strftime("%Y-%m-%d")
    lines = [
        f"# Store Opening SKU Analysis: {category}",
        f"",
        f"**Store type**: {store_type}  ",
        f"**Opening month**: {opening_month}  ",
        f"**Generated**: {now}",
        f"",
        f"---",
        f"",
        f"## Executive Summary",
        f"",
    ]

    if scored_skus:
        top = scored_skus[0]
        lines.append(
            f"Analyzed **{portfolio.get('total', len(scored_skus))} SKU candidates** "
            f"({portfolio.get('type_a_count', 0)} Type A + "
            f"{portfolio.get('type_b_count', 0)} Type B). "
            f"Top recommendation: **{top['name']}** (score {top['weighted_total']}/5)."
        )
    else:
        lines.append("No scored SKUs available.")

    if portfolio.get("warnings"):
        lines.extend(["", "**Warnings:**"])
        for w in portfolio["warnings"]:
            lines.append(f"- {w}")

    lines.extend([
        "",
        "---",
        "",
        "## Recommended SKU Lineup",
        "",
        "| Rank | SKU | Type | Price | Anchor | Margin | Score | Viral Hook |",
        "|------|-----|------|-------|--------|--------|-------|------------|",
    ])

    for sku in scored_skus:
        margin = sku.get("margin_analysis", {})
        m_pct = (
            f"{round(margin.get('conservative', 0)*100)}%"
            if margin.get("conservative") is not None
            else "unvalidated"
        )
        anchor = sku.get("anchor_price", "")
        anchor_str = f"¥{anchor} ({sku.get('anchor_source', '')})" if anchor else "N/A (Type B)"
        hook = sku.get("viral_hook", "—")
        lines.append(
            f"| {sku['rank']} | {sku['name']} | {sku.get('type','?')} "
            f"| ¥{sku.get('our_price','?')} | {anchor_str} "
            f"| {m_pct} | {sku['weighted_total']}/5 | {hook} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## Type A/B Classification",
        "",
        "### Type A: 大家已认的商品 + 价格跌破心理预期",
    ])
    type_a = [s for s in scored_skus if s.get("type") == "A"]
    if type_a:
        for sku in type_a:
            punch = sku.get("punch_analysis", {})
            lines.append(f"- **{sku['name']}**: {punch.get('note', '')}")
    else:
        lines.append("- None identified")

    lines.extend(["", "### Type B: 大家不认识的商品 + 价格公道 + 体验惊艳"])
    type_b = [s for s in scored_skus if s.get("type") == "B"]
    if type_b:
        for sku in type_b:
            lines.append(f"- **{sku['name']}**: {sku.get('notes', 'No anchor — pure experience play')}")
    else:
        lines.append("- None identified")

    lines.extend([
        "",
        "---",
        "",
        "## Cost Validation",
        "",
    ])
    if cost_validation:
        for keyword, data in cost_validation.items():
            summary = data.get("price_summary", {})
            lines.append(f"**{keyword}**")
            if summary.get("retail_min"):
                lines.append(
                    f"- Retail signals: ¥{summary['retail_min']}–¥{summary['retail_max']} "
                    f"({summary['retail_signals_count']} data points)"
                )
                lines.append(
                    f"- Est. wholesale: ¥{summary['est_wholesale_low']}–¥{summary['est_wholesale_high']} "
                    f"(confidence: {summary.get('confidence', 'LOW')})"
                )
            else:
                lines.append(f"- No structured price data found")
            lines.append("")
    else:
        lines.append("Cost validation not run. Use `--cost-check` for validation.")

    lines.extend([
        "",
        "---",
        "",
        "## Market Research Coverage",
        "",
    ])
    if market_research:
        for keyword, kw_data in market_research.items():
            lines.append(f"**{keyword}**")
            for platform, pdata in kw_data.items():
                status = pdata.get("status", "unknown") if isinstance(pdata, dict) else "done"
                lines.append(f"- {platform}: {status}")
            lines.append("")
    else:
        lines.append("Market research not included in this run.")

    lines.extend([
        "",
        "---",
        f"*Generated by store-opening-selection skill — {now}*",
    ])

    report = "\n".join(lines)
    if output_path:
        with open(output_path, "w") as f:
            f.write(report)
        return output_path
    return report


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Store opening SKU selection analysis orchestrator"
    )
    parser.add_argument("--category", help="Product category (e.g. 澳洲和牛)")
    parser.add_argument("--store", default="硬折扣超市", help="Store type")
    parser.add_argument("--city", default="一线城市", help="City tier")
    parser.add_argument("--month", default="", help="Opening month")
    parser.add_argument("--keywords", help="Comma-separated keywords (auto-derived from category if omitted)")
    parser.add_argument("--score-only", action="store_true", help="Score candidates from --input, skip research")
    parser.add_argument("--cost-check", action="store_true", help="Run cost validation only")
    parser.add_argument("--keyword", help="Single keyword for --cost-check")
    parser.add_argument("--input", help="JSON file with SKU candidates (for --score-only)")
    parser.add_argument("--output", help="Output JSON file path (default: stdout)")
    parser.add_argument("--report", help="Generate Markdown report to this path")
    parser.add_argument("--demo", action="store_true", help="Run wagyu demo")
    args = parser.parse_args()

    # ── Demo mode
    if args.demo:
        print("Running wagyu demo...", file=sys.stderr)
        scored = run_script("sku_scorer.py", ["--demo"])
        scored["meta"] = {"mode": "demo", "timestamp": datetime.now().isoformat()}
        if args.report:
            generate_report(scored, args.report)
            print(f"Report saved to {args.report}", file=sys.stderr)
        output = json.dumps(scored, ensure_ascii=False, indent=2)
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
        else:
            print(output)
        return

    # ── Cost check only
    if args.cost_check:
        keyword = args.keyword or args.category
        if not keyword:
            print('{"error": "provide --keyword or --category"}')
            sys.exit(1)
        result = run_cost_validation([keyword])
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # ── Score-only mode
    if args.score_only:
        if not args.input:
            print('{"error": "provide --input JSON file for --score-only"}')
            sys.exit(1)
        with open(args.input) as f:
            candidates = json.load(f)
        scored = run_sku_scoring(candidates)
        if args.report:
            generate_report(scored, args.report)
            print(f"Report saved to {args.report}", file=sys.stderr)
        output = json.dumps(scored, ensure_ascii=False, indent=2)
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
        else:
            print(output)
        return

    # ── Full workflow
    if not args.category:
        parser.print_help()
        sys.exit(1)

    keywords = [k.strip() for k in args.keywords.split(",")] if args.keywords else [args.category]

    result = {
        "category": args.category,
        "store_type": args.store,
        "city": args.city,
        "opening_month": args.month,
        "analysis_timestamp": datetime.now().isoformat(),
        "steps_completed": [],
    }

    print(f"[1/4] Running market research for: {keywords}", file=sys.stderr)
    result["market_research"] = run_market_research(keywords)
    result["steps_completed"].append("market_research")

    print("[2/4] Running cost validation...", file=sys.stderr)
    result["cost_validation"] = run_cost_validation(keywords)
    result["steps_completed"].append("cost_validation")

    print("[3/4] Generating SKU template for scoring...", file=sys.stderr)
    result["note"] = (
        "Full SKU scoring requires manual candidate input. "
        "Run with --score-only --input candidates.json after populating SKU data. "
        "See scripts/sku_scorer.py --demo for the expected input format."
    )
    result["steps_completed"].append("research_complete")

    if args.report:
        print(f"[4/4] Generating report to {args.report}", file=sys.stderr)
        generate_report(result, args.report)
        result["steps_completed"].append("report_generated")
        result["report_path"] = args.report

    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Results saved to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
