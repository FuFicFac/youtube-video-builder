"""Index installed Open Design examples into a searchable local HTML gallery."""
import argparse
import html
import json
import os
from pathlib import Path


def build(root, output):
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"Open Design root does not exist: {root}")
    examples = []
    systems = []
    for section in ("design-systems", "design-templates", "craft", "frames"):
        folder = root / section
        for path in sorted(folder.rglob("*.html")) if folder.exists() else []:
            design = next((p / "DESIGN.md" for p in (path.parent, *path.parents) if p == root or root in p.parents if (p / "DESIGN.md").is_file()), None)
            examples.append({"name": str(path.relative_to(root)), "url": path.as_uri(), "design": design.as_uri() if design else ""})
        for path in sorted(folder.rglob("DESIGN.md")) if folder.exists() else []:
            systems.append({"name": str(path.relative_to(root)), "url": path.as_uri()})
    if not examples:
        raise ValueError(f"No Open Design HTML examples found beneath {root}")
    payload = json.dumps({"examples": examples, "systems": systems}).replace("<", "\\u003c")
    page = """<!doctype html><html lang="en"><meta charset="utf-8"><title>Choose a video style</title>
<style>body{font:16px system-ui;margin:24px;background:#f5f3ee;color:#222}input{padding:12px;width:75%;font:inherit}a{color:#174c72}.layout{display:grid;grid-template-columns:minmax(300px,1fr) 2fr;gap:20px}#list{height:75vh;overflow:auto}article{padding:12px;border-bottom:1px solid #ccc}button{font:inherit;padding:8px;cursor:pointer}iframe{width:100%;height:75vh;background:white;border:1px solid #aaa}small{display:block;margin:5px 0}</style>
<h1>Choose a video style</h1><p>Select an example to preview, then choose its palette and visual style for the video. Open Design files stay on this machine.</p><input id="search" aria-label="Search styles" placeholder="Search styles"><p id="count"></p><div class="layout"><div id="list"></div><iframe id="preview" title="Selected design preview"></iframe></div><details><summary>Design system instructions</summary><div id="systems"></div></details><script>
const data=PAYLOAD;const list=document.getElementById('list');const preview=document.getElementById('preview');
function link(label,url){const a=document.createElement('a');a.textContent=label;a.href=url;a.target='_blank';return a}
function draw(){const q=document.getElementById('search').value.toLowerCase();list.replaceChildren();const shown=data.examples.filter(x=>x.name.toLowerCase().includes(q));document.getElementById('count').textContent=shown.length+' HTML examples; '+data.systems.length+' design references';for(const x of shown){const a=document.createElement('article');const b=document.createElement('button');b.textContent=x.name;b.onclick=()=>{preview.src=x.url};a.append(b);const s=document.createElement('small');s.append(link('Open example',x.url));if(x.design){s.append(' · ',link('Read DESIGN.md',x.design))}a.append(s);list.append(a)}}
document.getElementById('search').oninput=draw;for(const x of data.systems){const p=document.createElement('p');p.append(link(x.name,x.url));document.getElementById('systems').append(p)}draw();if(data.examples.length)preview.src=data.examples[0].url;
</script></html>""".replace("PAYLOAD", payload)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page)
    return {"root": str(root), "output": str(output.resolve()), "examples": len(examples), "design_references": len(systems)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    candidates = [args.root] if args.root else [Path(os.environ["OPEN_DESIGN_ROOT"])] if os.environ.get("OPEN_DESIGN_ROOT") else [Path("/Applications/Open Design.app/Contents/Resources/open-design"), Path.home() / "Open Design"]
    root = next((p for p in candidates if p and p.is_dir()), None)
    if root is None:
        parser.error("Open Design not found; supply --root or OPEN_DESIGN_ROOT")
    try:
        print(json.dumps(build(root, args.output), indent=2))
    except ValueError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
