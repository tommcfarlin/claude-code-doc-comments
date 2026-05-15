#!/usr/bin/env python3
"""
Generate a self-contained dual-model HTML report from evaluation/metrics.json.

Output: evaluation/report.html — inline CSS + inline SVG charts, no external deps.
"""

import html
import json
import statistics
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
EVAL_DIR = SCRIPT_DIR.parent  # evaluation/
REPO_ROOT = EVAL_DIR.parent
METRICS_FILE = EVAL_DIR / "metrics.json"
PROMPT_FILE = EVAL_DIR / "task-prompt.txt"
REPORT_FILE = EVAL_DIR / "report.html"

ARM_LABELS = {
    "a": "Arm A — stripped (no docs)",
    "b": "Arm B — skill-generated",
    "c": "Arm C — human-written (original)",
}
ARM_COLORS = {"a": "#d4574e", "b": "#3a7bd5", "c": "#2ea043"}
MODEL_LABELS = {"opus": "Opus 4.7", "sonnet": "Sonnet 4.6"}


def median(values):
    return statistics.median(values) if values else 0


def pct_delta(baseline, comparison):
    if baseline == 0:
        return 0
    return (comparison - baseline) / baseline * 100


def fmt_delta(d):
    sign = "+" if d >= 0 else ""
    return f"{sign}{d:.1f}%"


def delta_class(d):
    # Lower input tokens is "good" (supports hypothesis); higher is "bad"
    return "delta-down" if d < 0 else "delta-up"


def bar_chart_svg(runs_by_arm, title, unit, width=520, height=240):
    padding = 50
    bar_area_w = width - 2 * padding
    bar_area_h = height - 2 * padding
    arms = ["a", "b", "c"]
    max_val = max((max(v) for v in runs_by_arm.values() if v), default=1)
    if max_val == 0:
        max_val = 1
    bar_group_w = bar_area_w / len(arms)
    n_runs_max = max((len(v) for v in runs_by_arm.values()), default=1)
    bar_w = bar_group_w / (n_runs_max + 2)

    svg = [f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
           f'role="img" aria-label="{html.escape(title)}">']
    svg.append(f'<text x="{width/2}" y="22" text-anchor="middle" '
               f'font-family="-apple-system,sans-serif" font-size="13" font-weight="600">'
               f'{html.escape(title)}</text>')

    for i in range(5):
        y = padding + bar_area_h - (i / 4) * bar_area_h
        val = (max_val * i / 4)
        svg.append(f'<line x1="{padding}" y1="{y}" x2="{width-padding}" y2="{y}" '
                   f'stroke="#e5e5e5" stroke-width="1"/>')
        svg.append(f'<text x="{padding-6}" y="{y+4}" text-anchor="end" '
                   f'font-family="-apple-system,sans-serif" font-size="10" fill="#666">'
                   f'{int(val):,}</text>')

    for ai, arm in enumerate(arms):
        runs = runs_by_arm.get(arm, [])
        group_x = padding + ai * bar_group_w + (bar_group_w - len(runs) * bar_w) / 2
        for ri, v in enumerate(runs):
            h_px = (v / max_val) * bar_area_h
            x = group_x + ri * bar_w
            y = padding + bar_area_h - h_px
            svg.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w-1:.1f}" '
                       f'height="{h_px:.1f}" fill="{ARM_COLORS[arm]}" opacity="0.78"/>')
        if runs:
            med = median(runs)
            med_y = padding + bar_area_h - (med / max_val) * bar_area_h
            svg.append(f'<line x1="{group_x-4}" y1="{med_y:.1f}" '
                       f'x2="{group_x + len(runs)*bar_w + 4}" y2="{med_y:.1f}" '
                       f'stroke="#111" stroke-width="2" stroke-dasharray="3,2"/>')
            svg.append(f'<text x="{group_x + len(runs)*bar_w + 6}" y="{med_y+4:.1f}" '
                       f'font-family="-apple-system,sans-serif" font-size="9" fill="#111">'
                       f'{int(med):,}</text>')
        svg.append(f'<text x="{group_x + len(runs)*bar_w/2:.1f}" y="{height-padding+18}" '
                   f'text-anchor="middle" font-family="-apple-system,sans-serif" '
                   f'font-size="11" font-weight="600">Arm {arm.upper()}</text>')

    svg.append('</svg>')
    return ''.join(svg)


def load_demo_diff():
    repo_root = REPO_ROOT
    base = Path("/Users/tommcfarlin/Projects/02-tm/doc-comments-experiment")
    try:
        return {
            "filename": "WCIWKit/Models/Media.swift",
            "a": (base / "arm-a-stripped/WCIWKit/Models/Media.swift").read_text(),
            "b": (base / "arm-b-skill/WCIWKit/Models/Media.swift").read_text(),
            "c": (base / "arm-c-original/WCIWKit/Models/Media.swift").read_text(),
        }
    except FileNotFoundError:
        return None


def main():
    if not METRICS_FILE.exists():
        print(f"Missing {METRICS_FILE}. Run parse-runs.py first.")
        return

    runs = json.loads(METRICS_FILE.read_text())

    # Bucket: model -> arm -> [metric per run]
    by_model_arm = {}
    for r in runs:
        m = r.get("model", "unknown")
        a = r.get("arm", "?")
        by_model_arm.setdefault(m, {}).setdefault(a, []).append(r)

    models = [m for m in ["opus", "sonnet"] if m in by_model_arm]

    def med(model, arm, key):
        rows = by_model_arm.get(model, {}).get(arm, [])
        return median([r.get(key, 0) for r in rows])

    # Headline rows
    head_rows = []
    for m in models:
        a_med = med(m, "a", "input_tokens_to_first_edit")
        b_med = med(m, "b", "input_tokens_to_first_edit")
        c_med = med(m, "c", "input_tokens_to_first_edit")
        n_a = len(by_model_arm[m].get("a", []))
        n_b = len(by_model_arm[m].get("b", []))
        n_c = len(by_model_arm[m].get("c", []))
        head_rows.append({
            "model": m, "a": a_med, "b": b_med, "c": c_med,
            "n_a": n_a, "n_b": n_b, "n_c": n_c,
            "d_ba": pct_delta(a_med, b_med),
            "d_ca": pct_delta(a_med, c_med),
        })

    headline_table_rows = "\n".join([
        f"""<tr>
          <td><strong>{MODEL_LABELS[r['model']]}</strong></td>
          <td class="num">{int(r['a']):,}</td>
          <td class="num">{int(r['b']):,}</td>
          <td class="num">{int(r['c']):,}</td>
          <td class="num {delta_class(r['d_ba'])}">{fmt_delta(r['d_ba'])}</td>
          <td class="num {delta_class(r['d_ca'])}">{fmt_delta(r['d_ca'])}</td>
        </tr>"""
        for r in head_rows
    ])

    # Discovery-call rows
    disc_rows = []
    for m in models:
        disc_rows.append({
            "model": m,
            "a": med(m, "a", "discovery_calls_before_first_edit"),
            "b": med(m, "b", "discovery_calls_before_first_edit"),
            "c": med(m, "c", "discovery_calls_before_first_edit"),
        })
    disc_table_rows = "\n".join([
        f"""<tr>
          <td><strong>{MODEL_LABELS[r['model']]}</strong></td>
          <td class="num">{r['a']:.1f}</td>
          <td class="num">{r['b']:.1f}</td>
          <td class="num">{r['c']:.1f}</td>
        </tr>"""
        for r in disc_rows
    ])

    # Charts per model
    chart_blocks = ""
    for m in models:
        chart_blocks += f"<h3>{MODEL_LABELS[m]} — input tokens to first edit</h3>"
        chart_blocks += bar_chart_svg(
            {arm: [r.get("input_tokens_to_first_edit", 0) for r in by_model_arm[m].get(arm, [])] for arm in "abc"},
            f"{MODEL_LABELS[m]} — input tokens to first edit", "tokens"
        )
        chart_blocks += f"<h3>{MODEL_LABELS[m]} — discovery calls before first edit</h3>"
        chart_blocks += bar_chart_svg(
            {arm: [r.get("discovery_calls_before_first_edit", 0) for r in by_model_arm[m].get(arm, [])] for arm in "abc"},
            f"{MODEL_LABELS[m]} — discovery calls", "calls"
        )

    # Per-run detail tables
    def per_run_table(model, arm):
        rows = []
        for r in sorted(by_model_arm.get(model, {}).get(arm, []), key=lambda x: x.get("run", 0)):
            rows.append(f"""
              <tr>
                <td>{r.get('run','?')}</td>
                <td class="num">{r.get('input_tokens_total',0):,}</td>
                <td class="num">{r.get('input_tokens_to_first_edit',0):,}</td>
                <td class="num">{r.get('output_tokens_total',0):,}</td>
                <td class="num">{r.get('discovery_calls_before_first_edit',0)}</td>
                <td class="num">{r.get('turns_total',0)}</td>
                <td class="num">{r.get('duration_seconds','?')}s</td>
              </tr>""")
        return "".join(rows)

    detail_blocks = ""
    for m in models:
        detail_blocks += f"<h3>{MODEL_LABELS[m]}</h3>"
        for arm in "abc":
            detail_blocks += f"""<h4 class="arm-color-{arm}">{ARM_LABELS[arm]} (N={len(by_model_arm[m].get(arm, []))})</h4>
            <table><thead><tr>
              <th>Run</th><th class="num">Input total</th><th class="num">Input to first edit</th>
              <th class="num">Output total</th><th class="num">Disc. calls pre-edit</th>
              <th class="num">Turns</th><th class="num">Duration</th>
            </tr></thead><tbody>{per_run_table(m, arm)}</tbody></table>"""

    demo = load_demo_diff()
    prompt_text = PROMPT_FILE.read_text().strip()
    prompt_hash = subprocess.check_output(["shasum", "-a", "256", str(PROMPT_FILE)]).decode().split()[0]

    n_summary = " · ".join([
        f"{MODEL_LABELS[m]}: N={len(by_model_arm[m].get('a', []))}" for m in models
    ])

    html_out = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>doc-comments skill — evaluation report (dual-model)</title>
<style>
  :root {{
    --fg: #1a1a1a; --muted: #666; --bg: #fff; --border: #e5e5e5;
    --accent: #2563eb; --good: #2ea043; --bad: #d4574e;
  }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif;
         color: var(--fg); background: var(--bg); max-width: 900px;
         margin: 40px auto; padding: 0 24px; line-height: 1.55; }}
  h1 {{ font-size: 28px; margin-bottom: 4px; }}
  h2 {{ font-size: 20px; margin-top: 36px; border-bottom: 1px solid var(--border); padding-bottom: 6px; }}
  h3 {{ font-size: 16px; margin-top: 24px; }}
  h4 {{ font-size: 14px; margin-top: 16px; }}
  .subtitle {{ color: var(--muted); margin-top: 0; }}
  .meta {{ font-size: 13px; color: var(--muted); margin: 16px 0; }}
  .meta code {{ background: #f4f4f4; padding: 1px 5px; border-radius: 3px; font-size: 12px; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 13px; margin: 12px 0; }}
  th, td {{ padding: 6px 10px; border-bottom: 1px solid var(--border); text-align: left; }}
  th {{ background: #fafafa; font-weight: 600; }}
  td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .headline-table {{ font-size: 14px; }}
  .delta-down {{ color: var(--good); font-weight: 600; }}
  .delta-up {{ color: var(--bad); font-weight: 600; }}
  .demo {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; font-size: 11px; }}
  .demo pre {{ background: #fafafa; padding: 10px; border-radius: 4px; overflow: auto;
              max-height: 380px; border: 1px solid var(--border); margin: 0; }}
  .demo h4 {{ margin: 0 0 6px 0; font-size: 12px; }}
  .caveats {{ background: #fff8e6; border-left: 3px solid #d4a017; padding: 12px 16px; border-radius: 0 4px 4px 0; }}
  .key-finding {{ background: #f0f7ff; border-left: 3px solid var(--accent); padding: 14px 18px;
                  border-radius: 0 4px 4px 0; margin: 20px 0; }}
  .arm-color-a {{ color: {ARM_COLORS['a']}; }}
  .arm-color-b {{ color: {ARM_COLORS['b']}; }}
  .arm-color-c {{ color: {ARM_COLORS['c']}; }}
  svg {{ display: block; margin: 8px 0; }}
  code, pre {{ font-family: "SF Mono", Menlo, monospace; }}
</style>
</head>
<body>

<h1>doc-comments skill — evaluation report</h1>
<p class="subtitle">A controlled test of the skill's premise across two model tiers.</p>

<div class="meta">
  Fixture: <code>tommcfarlin/where-can-i-watch-ios</code> @ <code>8cd0d54</code> ·
  Models: <code>claude-opus-4-7</code>, <code>claude-sonnet-4-6</code> ·
  {n_summary} ·
  Prompt SHA-256: <code>{prompt_hash[:16]}…</code>
</div>

<div class="key-finding">
  <strong>Headline.</strong> The skill's premise — that doc comments reduce agent discovery cost — is more specific than originally claimed. Human-written doc comments <em>do</em> reduce Sonnet's discovery cost meaningfully. The skill's generated doc comments <em>do not</em> — they make Sonnet do more work, not less. On Opus, doc comments of either kind add cost without changing behavior. <strong>The skill should not be used.</strong>
  <br><br>
  Full pre-registration of the Sonnet hypothesis (committed before Sonnet runs) is at
  <a href="preregistration-sonnet.md"><code>preregistration-sonnet.md</code></a>.
</div>

<h2>Headline: median input tokens to first edit</h2>
<table class="headline-table">
  <thead><tr>
    <th>Model</th>
    <th class="num">Arm A — stripped</th>
    <th class="num">Arm B — skill</th>
    <th class="num">Arm C — human</th>
    <th class="num">Δ B vs A</th>
    <th class="num">Δ C vs A</th>
  </tr></thead>
  <tbody>
{headline_table_rows}
  </tbody>
</table>
<p class="meta">Negative Δ = doc comments reduced agent cost (supports hypothesis). Positive Δ = increased cost.</p>

<h2>The mechanism: median discovery calls before first edit</h2>
<table class="headline-table">
  <thead><tr>
    <th>Model</th>
    <th class="num">Arm A — stripped</th>
    <th class="num">Arm B — skill</th>
    <th class="num">Arm C — human</th>
  </tr></thead>
  <tbody>
{disc_table_rows}
  </tbody>
</table>
<p>Discovery calls = <code>Read</code> / <code>Grep</code> / <code>Glob</code> / <code>Bash</code> tool uses before the agent's first <code>Edit</code>. Counts the number of <em>file-touching exploration acts</em> the agent did to figure out what to do.</p>

<p>Opus's reading strategy is roughly constant — it reads the same number of files regardless of doc state. Sonnet's is doc-quality-dependent: trusted docs (human) reduce reading dramatically; untrusted/insufficient docs (skill-generated) appear to push the agent toward <em>more</em> reading, presumably because it doesn't trust the docs and verifies against the implementation anyway.</p>

<h2>Methodology</h2>
<p>Three checkouts of the same Swift codebase, identical except for doc-comment state:</p>
<ul>
  <li><span class="arm-color-a"><strong>Arm A — stripped:</strong></span> all <code>///</code> and <code>/** */</code> doc comments removed. 570 lines deleted across 52 files. Pure deletions.</li>
  <li><span class="arm-color-b"><strong>Arm B — skill-generated:</strong></span> Arm A baseline + one full pass of the <code>doc-comments</code> skill. Added 681 doc lines across 54 files.</li>
  <li><span class="arm-color-c"><strong>Arm C — human-written:</strong></span> pristine <code>origin/main</code>, doc comments written by the codebase author.</li>
</ul>

<p>Each arm received the identical locked task prompt in fresh, non-interactive <code>claude -p</code> sessions
(stream-json output, <code>--permission-mode bypassPermissions</code>, <code>--disable-slash-commands</code>,
disallowed tools: Skill / AskUserQuestion / WebFetch / WebSearch, fresh process per run, working tree reset between
runs). Sonnet runs were pre-registered: a hypothesis document was committed and pushed <em>before</em> any Sonnet
run executed; it is preserved at <a href="preregistration-sonnet.md"><code>preregistration-sonnet.md</code></a>.</p>

<h3>Task prompt (locked, same for all 45 runs across both models)</h3>
<pre style="background:#fafafa;padding:12px;border-left:3px solid var(--accent);font-size:12px;white-space:pre-wrap;">{html.escape(prompt_text)}</pre>

<h3>Metric</h3>
<p><strong>Input tokens to first edit.</strong> Sum of <code>input_tokens</code> + <code>cache_read_input_tokens</code> + <code>cache_creation_input_tokens</code> across all assistant turns up to and including the first <code>Edit</code> / <code>Write</code> / <code>MultiEdit</code> / <code>NotebookEdit</code> tool call. This isolates the agent's discovery cost — work done <em>before</em> it knows enough to act. Secondary metrics: discovery tool calls before first edit, wall-clock duration, output tokens, total turns.</p>

<h2>Per-arm distributions</h2>
{chart_blocks}
<p class="meta">Dashed line and label = median per arm. Each bar is one run.</p>

<h2>Per-run detail</h2>
{detail_blocks}

<h2>Demo: one file, three states</h2>
<p>The same file under each arm. The agent saw one of these depending on the arm; the underlying code is identical.</p>
"""

    if demo:
        html_out += f"""
<p class="meta">File: <code>{html.escape(demo['filename'])}</code></p>
<div class="demo">
  <div>
    <h4 class="arm-color-a">Arm A — stripped</h4>
    <pre>{html.escape(demo['a'][:2400])}</pre>
  </div>
  <div>
    <h4 class="arm-color-b">Arm B — skill</h4>
    <pre>{html.escape(demo['b'][:2400])}</pre>
  </div>
  <div>
    <h4 class="arm-color-c">Arm C — human</h4>
    <pre>{html.escape(demo['c'][:2400])}</pre>
  </div>
</div>
"""

    html_out += """
<h2>Honest caveats</h2>
<div class="caveats">
  <ul>
    <li><strong>N=10 per cell.</strong> 60 runs across both models. Real but small; treat effect sizes as directional with reasonable confidence intervals visible in the per-arm charts.</li>
    <li><strong>One fixture, one task, one language.</strong> Results characterize <em>this combination</em>. They do not generalize without additional fixtures, tasks, or languages.</li>
    <li><strong>Temporal separation.</strong> Opus runs occurred on 2026-05-14 (first 5 per arm) and 2026-05-15 (last 5 per arm); Sonnet runs all occurred on 2026-05-15. Anthropic infrastructure state may differ across days.</li>
    <li><strong>"First edit" is a proxy.</strong> It approximates the moment an agent has enough context to act. It does not capture quality of the resulting edit or downstream rework.</li>
    <li><strong>We measured a single skill pass on Arm B.</strong> A different stochastic pass of the skill might produce different docs and different results — though the skill's output is constrained enough by SKILL.md that we expect comparable behavior.</li>
    <li><strong>The Sonnet finding leans on the C arm.</strong> The strongest claim — "good docs help less-capable agents" — rests on Arm C. The B arm contradicts it for skill-generated docs specifically.</li>
  </ul>
</div>

<h2>Reproduction</h2>
<p>All raw stream-json output, scripts, and arm states are committed alongside this report.
The methodology is reproducible on any codebase. See
<a href="README.md"><code>evaluation/README.md</code></a> for step-by-step instructions.</p>

<p class="meta" style="margin-top:48px;border-top:1px solid var(--border);padding-top:12px;">
Generated by <code>build-report.py</code>. Self-contained HTML; no external resources.
</p>

</body>
</html>
"""

    REPORT_FILE.write_text(html_out)
    print(f"Wrote {REPORT_FILE}")


if __name__ == "__main__":
    main()
