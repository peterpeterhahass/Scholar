import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BACKEND_DIR = r"D:/Work/Scholar/backend"
sys.path.insert(0, BACKEND_DIR)

from pathlib import Path
from services.markdown_extractor.note_viewer import _resolve_image_urls, get_raw_notes_path

path = get_raw_notes_path()
print(f"Notes path: {path}")
print(f"Notes path exists: {path.exists()}")

if not path.exists():
    # fallback
    alt = Path(BACKEND_DIR) / "temp/extractor_output/academic_notes.md"
    print(f"Trying fallback: {alt}")
    print(f"Fallback exists: {alt.exists()}")
    if alt.exists():
        path = alt

raw = path.read_text(encoding="utf-8")
print(f"Raw length: {len(raw)}")

resolved = _resolve_image_urls(raw, "2e13b80d-fd1d-4fc9-b26d-9579c7a80654")
print(f"Resolved length: {len(resolved)}")

urls = re.findall(r"!\[[^\]]*\]\(/api/images/[^)]+\)", resolved)
print(f"Image URLs found: {len(urls)}")
for u in urls[:5]:
    print(f"  {u}")
