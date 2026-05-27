from __future__ import annotations

import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "scripts" / "code_structure_manifest.json"
OUTPUT = ROOT / "docs" / "code_structure.html"


def _load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _module_card(module: dict) -> str:
    return f"""
      <article class="module-card">
        <div class="meta">
          <span>{escape(module.get("area", ""))}</span>
          <span>{escape(module.get("status", ""))}</span>
        </div>
        <h2>{escape(module.get("path", ""))}</h2>
        <p>{escape(module.get("functions", ""))}</p>
      </article>
    """


def build_html(manifest: dict) -> str:
    modules = manifest.get("modules", [])
    grouped: dict[str, list[dict]] = {}
    for module in modules:
        grouped.setdefault(module.get("area", "Other"), []).append(module)

    group_html = []
    for area, area_modules in grouped.items():
        cards = "\n".join(_module_card(module) for module in area_modules)
        group_html.append(f"""
    <section>
      <h1>{escape(area)}</h1>
      <div class="grid">
        {cards}
      </div>
    </section>
        """)

    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ResearchDraft.ai Code Structure</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #102033;
      --muted: #5d6b7c;
      --line: #d9e2ec;
      --panel: #ffffff;
      --bg: #f5f8fb;
      --accent: #1f6feb;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      color: var(--ink);
      background: var(--bg);
      line-height: 1.55;
    }}
    header {{
      padding: 32px min(6vw, 72px);
      background: #ffffff;
      border-bottom: 1px solid var(--line);
    }}
    header h1 {{
      margin: 0 0 8px;
      font-size: clamp(28px, 4vw, 44px);
      letter-spacing: 0;
    }}
    header p {{
      max-width: 960px;
      margin: 0;
      color: var(--muted);
      font-size: 16px;
    }}
    main {{
      padding: 28px min(6vw, 72px) 48px;
    }}
    section {{
      margin: 0 0 34px;
    }}
    section > h1 {{
      margin: 0 0 14px;
      font-size: 22px;
      letter-spacing: 0;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 14px;
    }}
    .module-card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
      min-height: 172px;
    }}
    .module-card h2 {{
      margin: 10px 0 10px;
      font-size: 17px;
      line-height: 1.35;
      word-break: break-word;
    }}
    .module-card p {{
      margin: 0;
      color: var(--muted);
      font-size: 14px;
    }}
    .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      font-size: 12px;
      color: var(--accent);
    }}
    .meta span {{
      border: 1px solid rgba(31, 111, 235, 0.24);
      border-radius: 999px;
      padding: 3px 8px;
      background: rgba(31, 111, 235, 0.06);
    }}
    footer {{
      padding: 18px min(6vw, 72px);
      border-top: 1px solid var(--line);
      color: var(--muted);
      font-size: 13px;
      background: #ffffff;
    }}
  </style>
</head>
<body>
  <header>
    <h1>ResearchDraft.ai Code Structure</h1>
    <p>这个页面由 <code>scripts/update_code_structure_html.py</code> 根据 <code>scripts/code_structure_manifest.json</code> 自动生成，用来追踪从 <code>service.py</code> 拆分出去的 Python 模块位置和职责。</p>
  </header>
  <main>
    {"".join(group_html)}
  </main>
  <footer>
    Manifest updated: {escape(str(manifest.get("updated", "")))}. HTML generated: {generated_at}.
  </footer>
</body>
</html>
"""


def main() -> None:
    manifest = _load_manifest()
    OUTPUT.write_text(build_html(manifest), encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()

