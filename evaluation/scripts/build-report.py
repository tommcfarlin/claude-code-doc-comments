#!/usr/bin/env python3
"""
Generate a self-contained HTML report from results/metrics.json.

Output: results/report.html — inline CSS, inline SVG charts, no external deps.
"""

import html
import json
import statistics
import subprocess
from pathlib import Path

EXPERIMENT_DIR = Path("/Users/tommcfarlin/Projects/02-tm/doc-comments-experiment")
RESULTS_DIR = EXPERIMENT_DIR / "results"
METRICS_FILE = RESULTS_DIR / "metrics.json"
PROMPT_FILE = EXPERIMENT_DIR / "task-prompt.txt"
REPORT_FILE = RESULTS_DIR / "report.html"

ARM_LABELS = {
    "a": "Arm A — stripped (no docs)",
    "b": "Arm B — skill-generated",
    "c": "Arm C — human-written (original)",
}

ARM_COLORS = {"a": "#d4574e", "b": "#3a7bd5", "c": "#2ea043"}


def median(values):
    return statistics.median(values) if values else 0


def pct_delta(baseline, comparison):
    if baseline == 0:
        return 0
    return (comparison - baseline) / baseline * 100


def bar_chart_svg(values_by_arm, title, unit, width=520, height=240):
    """Render a simple grouped bar chart inline as SVG."""
    padding = 50
    bar_area_w = width - 2 * padding
    bar_area_h = height - 2 * padding
    arms = ["a", "b", "c"]
    max_val = max((max(v) for v in values_by_arm.values() if v), default=1)
    if max_val == 0:
        max_val = 1
    bar_group_w = bar_area_w / len(arms)
    bar_w = bar_group_w / 4

    svg = [f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
           f'role="img" aria-label="{html.escape(title)}">']
    svg.append(f'<text x="{width/2}" y="22" text-anchor="middle" '
               f'font-family="-apple-system,sans-serif" font-size="14" font-weight="600">'
               f'{html.escape(title)}</text>')

    # Y axis ticks
    for i in range(5):
        y = padding + bar_area_h - (i / 4) * bar_area_h
        val = (max_val * i / 4)
        svg.append(f'<line x1="{padding}" y1="{y}" x2="{width-padding}" y2="{y}" '
                   f'stroke="#e5e5e5" stroke-width="1"/>')
        svg.append(f'<text x="{padding-6}" y="{y+4}" text-anchor="end" '
                   f'font-family="-apple-system,sans-serif" font-size="10" fill="#666">'
                   f'{int(val):,}</text>')

    # Bars
    for ai, arm in enumerate(arms):
        runs = values_by_arm.get(arm, [])
        group_x = padding + ai * bar_group_w + (bar_group_w - 3 * bar_w) / 2
        for ri, v in enumerate(runs):
            h_px = (v / max_val) * bar_area_h
            x = group_x + ri * bar_w
            y = padding + bar_area_h - h_px
            svg.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w-2:.1f}" '
                       f'height="{h_px:.1f}" fill="{ARM_COLORS[arm]}" opacity="0.85"/>')
        # Median line
        if runs:
            med = median(runs)
            med_y = padding + bar_area_h - (med / max_val) * bar_area_h
            svg.append(f'<line x1="{group_x-4}" y1="{med_y:.1f}" '
                       f'x2="{group_x + 3*bar_w + 4}" y2="{med_y:.1f}" '
                       f'stroke="#222" stroke-width="2" stroke-dasharray="3,2"/>')
            svg.append(f'<text x="{group_x + 3*bar_w + 6}" y="{med_y+4:.1f}" '
                       f'font-family="-apple-system,sans-serif" font-size="10" fill="#222">'
                       f'med {int(med):,}</text>')
        # Arm label
        svg.append(f'<text x="{group_x + 3*bar_w/2:.1f}" y="{height-padding+18}" '
                   f'text-anchor="middle" font-family="-apple-system,sans-serif" '
                   f'font-size="11" font-weight="600">Arm {arm.upper()}</text>')

    svg.append(f'<text x="{padding-40}" y="{height/2}" text-anchor="middle" '
               f'font-family="-apple-system,sans-serif" font-size="10" fill="#666" '
               f'transform="rotate(-90 {padding-40},{height/2})">{html.escape(unit)}</text>')
    svg.append('</svg>')
    return ''.join(svg)


def load_demo_diff():
    """Pick one well-documented function and produce a 3-way diff for the demo."""
    arm_a = EXPERIMENT_DIR / "arm-a-stripped/WCIWKit/Models/Media.swift"
    arm_b = EXPERIMENT_DIR / "arm-b-skill/WCIWKit/Models/Media.swift"
    arm_c = EXPERIMENT_DIR / "arm-c-original/WCIWKit/Models/Media.swift"
    try:
        return {
            "filename": "WCIWKit/Models/Media.swift",
            "a": arm_a.read_text(),
            "b": arm_b.read_text(),
            "c": arm_c.read_text(),
        }
    except FileNotFoundError:
        return None


def main():
    if not METRICS_FILE.exists():
        print(f"Missing {METRICS_FILE}. Run parse-runs.py first.")
        return

    runs = json.loads(METRICS_FILE.read_text())
    runs_by_arm = {"a": [], "b": [], "c": []}
    for r in runs:
        arm = r.get("arm")
        if arm in runs_by_arm:
            runs_by_arm[arm].append(r)

    # Aggregates
    def med_metric(arm, key):
        vals = [r.get(key, 0) for r in runs_by_arm[arm] if r.get(key) is not None]
        return median(vals)

    summary = {}
    for arm in "abc":
        summary[arm] = {
            "n": len(runs_by_arm[arm]),
            "med_input_total": med_metric(arm, "input_tokens_total"),
            "med_input_to_edit": med_metric(arm, "input_tokens_to_first_edit"),
            "med_discovery_pre_edit": med_metric(arm, "discovery_calls_before_first_edit"),
            "med_duration": med_metric(arm, "duration_seconds"),
            "all_edited": all(r.get("made_an_edit", False) for r in runs_by_arm[arm]),
        }

    delta_a_vs_b = pct_delta(summary["a"]["med_input_to_edit"], summary["b"]["med_input_to_edit"])
    delta_a_vs_c = pct_delta(summary["a"]["med_input_to_edit"], summary["c"]["med_input_to_edit"])
    delta_b_vs_c = pct_delta(summary["c"]["med_input_to_edit"], summary["b"]["med_input_to_edit"])

    prompt_text = PROMPT_FILE.read_text().strip()
    prompt_hash = subprocess.check_output(["shasum", "-a", "256", str(PROMPT_FILE)]).decode().split()[0]

    chart_in_to_edit = bar_chart_svg(
        {arm: [r.get("input_tokens_to_first_edit", 0) for r in runs_by_arm[arm]] for arm in "abc"},
        "Input tokens consumed before first edit", "tokens"
    )
    chart_discovery = bar_chart_svg(
        {arm: [r.get("discovery_calls_before_first_edit", 0) for r in runs_by_arm[arm]] for arm in "abc"},
        "Discovery tool calls (Read/Grep/Glob/Bash) before first edit", "calls"
    )
    chart_duration = bar_chart_svg(
        {arm: [r.get("duration_seconds", 0) for r in runs_by_arm[arm]] for arm in "abc"},
        "Wall-clock time per run", "seconds"
    )

    demo = load_demo_diff()

    def runs_table(arm):
        rows = []
        for r in sorted(runs_by_arm[arm], key=lambda x: x.get("run", 0)):
            rows.append(f"""
              <tr>
                <td>{r.get('run','?')}</td>
                <td class="num">{r.get('input_tokens_total',0):,}</td>
                <td class="num">{r.get('input_tokens_to_first_edit',0):,}</td>
                <td class="num">{r.get('output_tokens_total',0):,}</td>
                <td class="num">{r.get('discovery_calls_before_first_edit',0)}</td>
                <td class="num">{r.get('turns_total',0)}</td>
                <td class="num">{r.get('duration_seconds','?')}s</td>
                <td>{'Yes' if r.get('made_an_edit') else 'No'}</td>
              </tr>""")
        return "\n".join(rows)

    html_out = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>doc-comments skill — evaluation report</title>
<style>
  :root {{
    --fg: #1a1a1a; --muted: #666; --bg: #fff; --border: #e5e5e5;
    --accent: #2563eb; --good: #2ea043; --bad: #d4574e;
  }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif;
         color: var(--fg); background: var(--bg); max-width: 880px;
         margin: 40px auto; padding: 0 24px; line-height: 1.55; }}
  h1 {{ font-size: 28px; margin-bottom: 4px; }}
  h2 {{ font-size: 20px; margin-top: 36px; border-bottom: 1px solid var(--border); padding-bottom: 6px; }}
  h3 {{ font-size: 16px; margin-top: 24px; }}
  .subtitle {{ color: var(--muted); margin-top: 0; }}
  .meta {{ font-size: 13px; color: var(--muted); margin: 16px 0; }}
  .meta code {{ background: #f4f4f4; padding: 1px 5px; border-radius: 3px; font-size: 12px; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 13px; margin: 12px 0; }}
  th, td {{ padding: 6px 10px; border-bottom: 1px solid var(--border); text-align: left; }}
  th {{ background: #fafafa; font-weight: 600; }}
  td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .headline {{ display: flex; gap: 16px; margin: 24px 0; flex-wrap: wrap; }}
  .stat {{ flex: 1; min-width: 200px; padding: 16px; border: 1px solid var(--border);
          border-radius: 6px; background: #fafafa; }}
  .stat .label {{ font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; }}
  .stat .value {{ font-size: 24px; font-weight: 600; margin: 4px 0; }}
  .stat .sub {{ font-size: 12px; color: var(--muted); }}
  .delta-down {{ color: var(--good); }}
  .delta-up {{ color: var(--bad); }}
  .demo {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; font-size: 11px; }}
  .demo pre {{ background: #fafafa; padding: 10px; border-radius: 4px; overflow: auto;
              max-height: 360px; border: 1px solid var(--border); margin: 0; }}
  .demo h4 {{ margin: 0 0 6px 0; font-size: 12px; }}
  .caveats {{ background: #fff8e6; border-left: 3px solid #d4a017; padding: 12px 16px; border-radius: 0 4px 4px 0; }}
  .arm-color-a {{ color: {ARM_COLORS['a']}; }}
  .arm-color-b {{ color: {ARM_COLORS['b']}; }}
  .arm-color-c {{ color: {ARM_COLORS['c']}; }}
  svg {{ display: block; margin: 8px 0; }}
  code, pre {{ font-family: "SF Mono", Menlo, monospace; }}
</style>
</head>
<body>

<h1>doc-comments skill — evaluation report</h1>
<p class="subtitle">Does an agent measurably need fewer tokens to understand a codebase that has structured doc comments?</p>

<div class="meta">
  Fixture: <code>tommcfarlin/where-can-i-watch-ios</code> @ <code>8cd0d54</code> ·
  Model: <code>claude-opus-4-7</code> ·
  N = {summary['a']['n']} runs per arm ·
  Prompt SHA-256: <code>{prompt_hash[:16]}…</code>
</div>

{'<div class="caveats" style="background:#fef0f0;border-left-color:#d4574e;"><strong>PRELIMINARY.</strong> This pass ran with N=' + str(summary['a']['n']) + ' per arm due to budget constraints. Within-arm variance is comparable to between-arm differences at this N — treat all deltas as directional only. A full N=5 pass is planned.</div>' if summary['a']['n'] < 3 else ''}

<h2>Headline</h2>
<div class="headline">
  <div class="stat">
    <div class="label">Skill vs. no docs</div>
    <div class="value {'delta-down' if delta_a_vs_b < 0 else 'delta-up'}">{delta_a_vs_b:+.1f}%</div>
    <div class="sub">median input tokens to first edit, Arm B vs. Arm A</div>
  </div>
  <div class="stat">
    <div class="label">Human docs vs. no docs</div>
    <div class="value {'delta-down' if delta_a_vs_c < 0 else 'delta-up'}">{delta_a_vs_c:+.1f}%</div>
    <div class="sub">median input tokens to first edit, Arm C vs. Arm A</div>
  </div>
  <div class="stat">
    <div class="label">Skill vs. human</div>
    <div class="value">{delta_b_vs_c:+.1f}%</div>
    <div class="sub">median input tokens to first edit, Arm B vs. Arm C</div>
  </div>
</div>

<h2>Methodology</h2>
<p>Three checkouts of the same Swift codebase, identical except for doc-comment state:</p>
<ul>
  <li><span class="arm-color-a"><strong>Arm A — stripped:</strong></span> all <code>///</code> and <code>/** */</code> doc comments removed. 570 doc lines deleted across 52 files. Pure deletions; no code, formatting, or whitespace modified.</li>
  <li><span class="arm-color-b"><strong>Arm B — skill-generated:</strong></span> Arm A's stripped baseline, then one full pass of the <code>doc-comments</code> skill. Generated 681 doc lines across 54 files.</li>
  <li><span class="arm-color-c"><strong>Arm C — human-written (original):</strong></span> pristine <code>origin/main</code>. Hand-written doc comments by the codebase author.</li>
</ul>
<p>Each arm received the identical task prompt below in 3 fresh, non-interactive <code>claude -p</code> sessions
(stream-json output, <code>--permission-mode bypassPermissions</code>, fresh process per run, working tree
reset between runs). 9 runs total. Same model, same prompt, no shared context.</p>

<h3>Task prompt (locked)</h3>
<pre style="background:#fafafa;padding:12px;border-left:3px solid var(--accent);font-size:12px;white-space:pre-wrap;">{html.escape(prompt_text)}</pre>

<h3>Metric: input tokens before first edit</h3>
<p>"First edit" is defined as the first Claude tool call to <code>Edit</code>, <code>Write</code>, <code>MultiEdit</code>,
or <code>NotebookEdit</code>. All input tokens (including cache reads and cache creation) consumed up to and
including that turn are summed. This isolates discovery cost — the work the agent does <em>before</em> it knows
enough to start acting.</p>

<h2>Results</h2>

<h3>Input tokens to first edit</h3>
{chart_in_to_edit}
<p class="meta">Dashed line = median per arm. Each bar = one run.</p>

<h3>Discovery tool calls (Read / Grep / Glob / Bash) before first edit</h3>
{chart_discovery}

<h3>Wall-clock time per run</h3>
{chart_duration}

<h2>Per-run detail</h2>

<h3 class="arm-color-a">Arm A — stripped (no docs)</h3>
<table>
  <thead><tr>
    <th>Run</th><th class="num">Input total</th><th class="num">Input to first edit</th>
    <th class="num">Output total</th><th class="num">Disc. calls pre-edit</th>
    <th class="num">Turns</th><th class="num">Duration</th><th>Edited?</th>
  </tr></thead>
  <tbody>{runs_table('a')}</tbody>
</table>

<h3 class="arm-color-b">Arm B — skill-generated</h3>
<table>
  <thead><tr>
    <th>Run</th><th class="num">Input total</th><th class="num">Input to first edit</th>
    <th class="num">Output total</th><th class="num">Disc. calls pre-edit</th>
    <th class="num">Turns</th><th class="num">Duration</th><th>Edited?</th>
  </tr></thead>
  <tbody>{runs_table('b')}</tbody>
</table>

<h3 class="arm-color-c">Arm C — human-written (original)</h3>
<table>
  <thead><tr>
    <th>Run</th><th class="num">Input total</th><th class="num">Input to first edit</th>
    <th class="num">Output total</th><th class="num">Disc. calls pre-edit</th>
    <th class="num">Turns</th><th class="num">Duration</th><th>Edited?</th>
  </tr></thead>
  <tbody>{runs_table('c')}</tbody>
</table>

<h2>Demo: one file, three states</h2>
<p>The same file under all three arms. The agent sees one of these depending on the arm; the code is identical.</p>
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

    html_out += f"""
<h2>Honest caveats</h2>
<div class="caveats">
  <ul>
    <li><strong>N = 3 per arm.</strong> 9 runs total. This is directional, not statistically significant. Variance within an arm is real and visible in the per-run tables.</li>
    <li><strong>One fixture, one task, one language.</strong> Results characterize <em>this</em> codebase and <em>this</em> task. They do not generalize without additional fixtures.</li>
    <li><strong>"First edit" is a proxy.</strong> It approximates the moment an agent has enough context to act. It does not capture quality of the resulting edit or downstream rework.</li>
    <li><strong>Same model for all arms.</strong> Opus 4.7. A weaker model would likely show larger deltas; a stronger model would show smaller ones.</li>
    <li><strong>The skill's own output is being measured against itself's premise.</strong> The skill was authored with this exact hypothesis in mind. The experiment falsifies or supports the premise; it does not prove the skill is optimal at producing the docs it produces.</li>
  </ul>
</div>

<h2>Reproduction</h2>
<p>This experiment is reproducible from any fork of the fixture repo. The harness, strip script, and parse/report
scripts are committed to the doc-comments skill repo at
<code>experiments/where-can-i-watch-ios/</code>. To re-run:</p>
<pre style="background:#fafafa;padding:12px;font-size:12px;">git clone https://github.com/tommcfarlin/where-can-i-watch-ios.git
cd where-can-i-watch-ios
# Set up three worktrees per arm, apply strip script to Arm A & B,
# run /doc-comments on Arm B, then:
./run-experiment.sh
python3 parse-runs.py
python3 build-report.py</pre>

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
