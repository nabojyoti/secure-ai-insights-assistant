from pathlib import Path
from textwrap import wrap


ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "data" / "pdf"
PAGE_WIDTH = 95
LINES_PER_PAGE = 38


def pdf_escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .replace("\r", "")
    )


def text_to_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            lines.append("")
            continue
        lines.extend(wrap(stripped, width=PAGE_WIDTH, replace_whitespace=False) or [""])
    return lines


def build_page_object(page_id: int, contents_id: int) -> str:
    return (
        f"{page_id} 0 obj\n"
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        "/Resources << /Font << /F1 3 0 R >> >> "
        f"/Contents {contents_id} 0 R >>\n"
        "endobj\n"
    )


def build_content_object(object_id: int, lines: list[str], page_number: int) -> str:
    commands = ["BT", "/F1 10 Tf", "72 748 Td"]
    for index, line in enumerate(lines):
        if index > 0:
            commands.append("0 -16 Td")
        commands.append(f"({pdf_escape(line)}) Tj")
    commands.append("ET")
    stream = "\n".join(commands)
    return (
        f"{object_id} 0 obj\n"
        f"<< /Length {len(stream.encode('utf-8'))} >>\n"
        "stream\n"
        f"{stream}\n"
        "endstream\n"
        "endobj\n"
    )


def write_pdf(path: Path, text: str) -> None:
    all_lines = text_to_lines(text)
    if not all_lines:
        all_lines = [path.stem.replace("_", " ").title()]

    pages = [
        all_lines[index : index + LINES_PER_PAGE]
        for index in range(0, len(all_lines), LINES_PER_PAGE)
    ]

    page_ids = []
    objects = [
        "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        "",  # pages object is filled after page ids are known
        "3 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
    ]

    next_id = 4
    for page_number, page_lines in enumerate(pages, start=1):
        page_id = next_id
        content_id = next_id + 1
        next_id += 2
        page_ids.append(page_id)
        objects.append(build_page_object(page_id, content_id))
        objects.append(build_content_object(content_id, page_lines, page_number))

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[1] = f"2 0 obj\n<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>\nendobj\n"

    content = "%PDF-1.4\n"
    offsets = [0]
    for obj in objects:
        offsets.append(len(content.encode("utf-8")))
        content += obj

    xref_at = len(content.encode("utf-8"))
    content += f"xref\n0 {len(objects) + 1}\n"
    content += "0000000000 65535 f \n"
    for offset in offsets[1:]:
        content += f"{offset:010d} 00000 n \n"
    content += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_at}\n%%EOF\n"
    path.write_text(content, encoding="utf-8")


def main() -> None:
    txt_files = sorted(PDF_DIR.glob("*.txt"))
    if not txt_files:
        print(f"No .txt files found in {PDF_DIR}")
        return

    for txt_path in txt_files:
        pdf_path = txt_path.with_suffix(".pdf")
        write_pdf(pdf_path, txt_path.read_text(encoding="utf-8"))
        print(f"Updated {pdf_path.relative_to(ROOT)} from {txt_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
