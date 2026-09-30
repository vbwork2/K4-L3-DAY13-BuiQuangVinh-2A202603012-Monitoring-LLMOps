from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
from statistics import mean

import yaml

from . import logging_config
from .metrics import percentile


CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "dashboard.yaml"


def _recent_records(minutes: int) -> list[dict]:
    if not logging_config.LOG_PATH.exists():
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    records = []
    for line in logging_config.LOG_PATH.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
            timestamp = datetime.fromisoformat(record["ts"].replace("Z", "+00:00"))
            if timestamp >= cutoff:
                records.append(record)
        except (ValueError, KeyError, TypeError):
            continue
    return records


def _bars(values: list[float], color: str) -> str:
    maximum = max(values, default=0) or 1
    width = 560 / max(len(values), 1)
    rectangles = []
    for index, value in enumerate(values):
        height = value / maximum * 72
        rectangles.append(
            f'<rect x="{index * width:.1f}" y="{76 - height:.1f}" '
            f'width="{max(width - 2, 1):.1f}" height="{height:.1f}" fill="{color}" />'
        )
    return f'<svg viewBox="0 0 560 80" preserveAspectRatio="none" aria-label="Trend by minute">{"".join(rectangles)}</svg>'


def render_dashboard() -> str:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))["dashboard"]
    minutes = config["time_range_minutes"]
    records = _recent_records(minutes)
    received = [r for r in records if r.get("event") == "request_received"]
    sent = [r for r in records if r.get("event") == "response_sent"]
    failed = [r for r in records if r.get("event") == "request_failed"]
    latencies = [r["latency_ms"] for r in sent if isinstance(r.get("latency_ms"), (int, float))]
    ttfts = [r["ttft_ms"] for r in sent if isinstance(r.get("ttft_ms"), (int, float))]
    costs = [r.get("cost_usd", 0) for r in sent]
    qualities = [r["quality_score"] for r in sent if isinstance(r.get("quality_score"), (int, float))]
    retrieval = [r["tool_success"] for r in records if r.get("tool_name") == "retrieval" and isinstance(r.get("tool_success"), bool)]
    error_rate = 100 * len(failed) / len(received) if received else 0
    retrieval_rate = 100 * sum(retrieval) / len(retrieval) if retrieval else 0
    error_types = Counter(r.get("error_type", "unknown") for r in failed)
    by_minute = defaultdict(lambda: {"requests": 0, "cost": 0.0})
    for record in records:
        bucket = record["ts"][:16]
        if record.get("event") == "request_received":
            by_minute[bucket]["requests"] += 1
        elif record.get("event") == "response_sent":
            by_minute[bucket]["cost"] += record.get("cost_usd", 0)
    buckets = [by_minute[key] for key in sorted(by_minute)]
    panels = {panel["id"]: panel for panel in config["panels"]}

    def card(panel_id: str, body: str, trend: str = "") -> str:
        panel = panels[panel_id]
        threshold = panel["threshold"]
        return (
            '<section class="card">'
            f'<h2>{escape(panel["title"])}</h2>{body}{trend}'
            f'<p class="threshold">Threshold: {escape(str(threshold["aggregation"]))} '
            f'{escape(str(threshold["operator"]))} {threshold["value"]} '
            f'{escape(panel["unit"])}</p></section>'
        )

    latency = card(
        "latency",
        f'<div class="stat">P50 {percentile(latencies, 50):.0f} ms &nbsp; P95 {percentile(latencies, 95):.0f} ms</div>'
        f'<p>P99 {percentile(latencies, 99):.0f} ms · TTFT P95 {percentile(ttfts, 95):.0f} ms</p>',
    )
    traffic = card(
        "traffic",
        f'<div class="stat">{len(received)} requests</div><p>{len(received) / minutes:.2f} requests/minute</p>',
        _bars([item["requests"] for item in buckets], "#3b82f6"),
    )
    errors = card(
        "errors",
        f'<div class="stat">{error_rate:.1f}% error rate</div>'
        f'<p>Retrieval success {retrieval_rate:.1f}% ({sum(retrieval)}/{len(retrieval)})</p>'
        f'<p>Error types: {escape(", ".join(f"{key}: {value}" for key, value in error_types.items()) or "none")}</p>',
    )
    cost = card(
        "cost",
        f'<div class="stat">${sum(costs):.4f}</div><p>Total USD in window</p>',
        _bars([item["cost"] for item in buckets], "#10b981"),
    )
    tokens_in = sum(r.get("tokens_in", 0) for r in sent)
    tokens_out = sum(r.get("tokens_out", 0) for r in sent)
    tokens = card(
        "tokens",
        f'<div class="stat">{tokens_in:,} input</div><p>{tokens_out:,} output tokens</p>',
    )
    quality = card(
        "quality",
        f'<div class="stat">{mean(qualities):.2f}</div><p>Mean quality proxy from {len(qualities)} responses</p>' if qualities
        else '<div class="stat">No data</div><p>Run the workload to populate this panel.</p>',
    )
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta http-equiv="refresh" content="{config['refresh_seconds']}">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(config['title'])}</title>
<style>
body{{font-family:Segoe UI,Arial,sans-serif;background:#f3f6fb;color:#14263d;margin:0;padding:28px}}
main{{max-width:1260px;margin:auto}}h1{{font-size:28px;margin:0 0 8px}}h2{{font-size:17px;margin:0 0 22px}}
.meta{{color:#53657d;margin-bottom:24px}}.grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}}
.card{{background:white;border:1px solid #dce4ef;border-radius:14px;padding:22px;min-height:200px;box-shadow:0 2px 10px #14263d0a}}
.stat{{font-size:27px;font-weight:700}}p{{color:#53657d}}.threshold{{border-top:1px solid #e3e9f1;padding-top:14px;font-size:13px}}
svg{{width:100%;height:60px;margin-top:10px}}@media(max-width:900px){{.grid{{grid-template-columns:1fr}}}}
</style></head><body><main><h1>{escape(config['title'])}</h1>
<p class="meta">Source: data/logs.jsonl · Last {minutes} minutes · Refresh every {config['refresh_seconds']} seconds · Updated {updated}</p>
<div class="grid">{latency}{traffic}{errors}{cost}{tokens}{quality}</div></main></body></html>"""
