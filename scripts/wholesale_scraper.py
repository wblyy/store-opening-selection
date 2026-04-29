#!/usr/bin/env python3
"""
Wholesale cost scraper for store opening SKU validation.
Searches wholesale platforms (惠农网, 1688 suggest, JD reverse) for cost estimates.

Addresses the #1 pitfall from wagyu case: single-source costs can be off by 3x.
Always returns multiple sources so caller can cross-validate.

Usage:
    python3 wholesale_scraper.py --keyword "澳洲和牛 M5 上脑" --limit 10
    python3 wholesale_scraper.py --keyword "有机草莓 500g" --sources huinong,jd

Output: JSON to stdout with cost estimates per source.
"""
import argparse
import json
import sys
import urllib.parse
import urllib.request
import urllib.error
import ssl
import time
import re

ssl._create_default_https_context = ssl._create_unverified_context

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def fetch(url, headers=None, timeout=10):
    h = {"User-Agent": USER_AGENT}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return None
    except Exception:
        return None


# ─────────────────────────────────────────────
# Source: Taobao suggest (demand proxy + price signals)
# ─────────────────────────────────────────────

def scrape_taobao_suggest(keyword):
    """
    Taobao autocomplete API — no auth needed.
    Returns related search terms that signal price ranges consumers expect.
    """
    url = (
        "https://suggest.taobao.com/sug"
        f"?code=utf-8&q={urllib.parse.quote(keyword)}&area=c2c"
    )
    html = fetch(url)
    if not html:
        return {"source": "taobao_suggest", "status": "failed", "results": []}

    try:
        data = json.loads(html)
        suggestions = [item[0] for item in data.get("result", [])]
        # Extract price hints from suggestions like "澳洲和牛 M5 上脑 100元"
        price_hints = []
        for s in suggestions:
            m = re.search(r"(\d+)\s*元", s)
            if m:
                price_hints.append(int(m.group(1)))

        return {
            "source": "taobao_suggest",
            "status": "ok",
            "suggestions": suggestions[:10],
            "price_hints_yuan": price_hints,
            "note": "Consumer search terms — infer price expectations from language",
        }
    except Exception as e:
        return {"source": "taobao_suggest", "status": "error", "error": str(e)}


# ─────────────────────────────────────────────
# Source: JD price reverse (retail → estimate wholesale)
# ─────────────────────────────────────────────

def scrape_jd_search(keyword, limit=5):
    """
    JD search for retail prices. Wholesale ≈ retail × 0.4–0.55 for fresh/import.
    NOTE: JD anti-bot is moderate. Results may be partial.
    """
    url = (
        "https://search.jd.com/Search"
        f"?keyword={urllib.parse.quote(keyword)}&enc=utf-8&wq={urllib.parse.quote(keyword)}"
    )
    html = fetch(url, headers={"Referer": "https://www.jd.com/"})
    if not html:
        return {"source": "jd", "status": "failed", "results": []}

    # Extract product titles and prices via regex (avoids JS-rendered content)
    prices = re.findall(r'"price"\s*:\s*"([\d.]+)"', html)
    titles = re.findall(r'"name"\s*:\s*"([^"]{5,80})"', html)

    items = []
    for i, price in enumerate(prices[:limit]):
        item = {
            "retail_price_yuan": float(price),
            "title": titles[i] if i < len(titles) else "",
            "est_wholesale_low": round(float(price) * 0.40, 1),
            "est_wholesale_high": round(float(price) * 0.55, 1),
        }
        items.append(item)

    if not items:
        return {
            "source": "jd",
            "status": "blocked_or_empty",
            "note": "JD blocked JS-rendered results. Use browser CLI for better results.",
            "fallback": (
                f'browser navigate "https://search.jd.com/Search?keyword='
                f'{urllib.parse.quote(keyword)}" then browser extract "product prices"'
            ),
        }

    return {
        "source": "jd",
        "status": "ok",
        "items": items,
        "note": "Wholesale estimate = retail × 0.40–0.55 (fresh/import rule of thumb)",
        "warning": "Cross-validate with direct B2B source. JD→wholesale ratio varies.",
    }


# ─────────────────────────────────────────────
# Source: 惠农网 search (B2B agricultural wholesale)
# ─────────────────────────────────────────────

def scrape_huinong(keyword, limit=5):
    """
    惠农网 — best for fresh produce, imported meat, premium ingredients.
    Search results include wholesale price ranges and supplier info.
    NOTE: Listings may be stale. Check posting date in results.
    """
    url = (
        f"https://www.huinong.com/search/?searchType=product"
        f"&searchText={urllib.parse.quote(keyword)}&pageNum=1&pageSize={limit}"
    )
    html = fetch(url, headers={"Referer": "https://www.huinong.com/"})
    if not html:
        return {"source": "huinong", "status": "failed", "results": []}

    # Extract price ranges from HTML
    prices = re.findall(
        r'(?:单价|价格|批发价)[：:]\s*([¥￥]?\d+(?:\.\d+)?(?:\s*[-~至到]\s*\d+(?:\.\d+)?)?)',
        html
    )
    product_names = re.findall(r'<[^>]*class="[^"]*(?:name|title)[^"]*"[^>]*>([^<]{3,60})<', html)
    units = re.findall(r'(?:元/|每)(斤|kg|公斤|100g|500g|件|箱|袋)', html)

    items = []
    for i, price in enumerate(prices[:limit]):
        items.append({
            "price_range": price.replace("¥", "").replace("￥", "").strip(),
            "product": product_names[i].strip() if i < len(product_names) else keyword,
            "unit": units[i] if i < len(units) else "unknown",
        })

    if not items:
        return {
            "source": "huinong",
            "status": "no_structured_data",
            "note": "惠农网 layout may have changed. Try browser navigation.",
            "fallback": (
                f'browser navigate "https://www.huinong.com/search/?searchText='
                f'{urllib.parse.quote(keyword)}" then browser extract "wholesale prices"'
            ),
            "raw_price_hints": re.findall(r"\d+(?:\.\d+)?(?=\s*元)", html)[:10],
        }

    return {
        "source": "huinong",
        "status": "ok",
        "items": items,
        "warning": (
            "惠农网 listings may be months old. "
            "Verify freshness before using in margin calculations."
        ),
    }


# ─────────────────────────────────────────────
# Source: 1688 suggest API (B2B market signal)
# ─────────────────────────────────────────────

def scrape_1688_suggest(keyword):
    """
    1688 autocomplete — signals what B2B buyers search for.
    Does NOT return prices (search results require login + captcha).
    Useful for understanding available wholesale variants.
    """
    url = (
        "https://suggest.1688.com/suggest/suggestNew.do"
        f"?suggest={urllib.parse.quote(keyword)}&sf=Y&site=china"
    )
    html = fetch(url, headers={"Referer": "https://www.1688.com/"})
    if not html:
        return {"source": "1688_suggest", "status": "failed"}

    try:
        # 1688 returns JSONP or JSON
        clean = re.sub(r'^[^{]*', '', html).rstrip(");")
        data = json.loads(clean) if clean.startswith("{") else {}
        suggestions = []
        for item in data.get("result", {}).get("suggests", []):
            if isinstance(item, dict):
                suggestions.append(item.get("word", ""))
            elif isinstance(item, str):
                suggestions.append(item)
        return {
            "source": "1688_suggest",
            "status": "ok",
            "suggestions": suggestions[:10],
            "note": "B2B buyer search terms — signals available wholesale variants",
        }
    except Exception:
        return {
            "source": "1688_suggest",
            "status": "parse_failed",
            "note": "1688 suggest format may have changed. Use browser for full results.",
            "fallback": (
                f'browser navigate "https://s.1688.com/selloffer/offerlist.htm?keywords='
                f'{urllib.parse.quote(keyword)}" — requires login for prices'
            ),
        }


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

SOURCES = {
    "taobao": scrape_taobao_suggest,
    "jd": scrape_jd_search,
    "huinong": scrape_huinong,
    "1688": scrape_1688_suggest,
}


def main():
    parser = argparse.ArgumentParser(
        description="Wholesale cost scraper for store opening SKU validation"
    )
    parser.add_argument("--keyword", required=True, help="Product keyword to research")
    parser.add_argument(
        "--sources",
        default="taobao,jd,huinong,1688",
        help="Comma-separated list of sources (default: all)",
    )
    parser.add_argument("--limit", type=int, default=5, help="Max results per source")
    args = parser.parse_args()

    active_sources = [s.strip() for s in args.sources.split(",")]
    results = {"keyword": args.keyword, "sources": {}}

    for source_name in active_sources:
        if source_name not in SOURCES:
            results["sources"][source_name] = {"status": "unknown_source"}
            continue
        fn = SOURCES[source_name]
        if source_name in ("jd", "huinong"):
            data = fn(args.keyword, limit=args.limit)
        else:
            data = fn(args.keyword)
        results["sources"][source_name] = data
        time.sleep(0.5)  # polite rate limiting

    # Summary: extract all price signals across sources
    all_prices = []
    for source_data in results["sources"].values():
        if isinstance(source_data, dict):
            for item in source_data.get("items", []):
                if "retail_price_yuan" in item:
                    all_prices.append(item["retail_price_yuan"])
            for hint in source_data.get("price_hints_yuan", []):
                all_prices.append(hint)

    if all_prices:
        results["price_summary"] = {
            "retail_signals_count": len(all_prices),
            "retail_min": min(all_prices),
            "retail_max": max(all_prices),
            "est_wholesale_low": round(min(all_prices) * 0.40, 1),
            "est_wholesale_high": round(max(all_prices) * 0.55, 1),
            "confidence": "LOW — retail reverse estimate only. Get direct B2B quotes.",
        }
    else:
        results["price_summary"] = {
            "retail_signals_count": 0,
            "note": "No structured price data found. Use browser CLI for manual extraction.",
        }

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
