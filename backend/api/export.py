"""故事导出 — TXT / HTML / EPUB"""
import io
import zipfile
import uuid
from xml.etree.ElementTree import Element, SubElement, tostring
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from backend.memory import story_db

router = APIRouter()

EPUB_MIMETYPE = "application/epub+zip"
TXT_MIMETYPE = "text/plain; charset=utf-8"
HTML_MIMETYPE = "text/html; charset=utf-8"


async def _load_full_story(story_id: str):
    data = await story_db.load_story(story_id)
    if not data:
        raise HTTPException(status_code=404, detail="故事不存在")
    chapters = await story_db.load_all_chapters(story_id)
    return data, sorted(chapters, key=lambda c: c.get("chapter_number", 0))


@router.get("/{story_id}/export")
async def export_story(
    story_id: str,
    format: str = Query("txt", pattern="^(txt|html|epub)$"),
):
    data, chapters = await _load_full_story(story_id)
    cfg = data.get("config", {})
    title = (cfg.get("title") or data.get("title") or "未命名").strip()
    meta = f"{cfg.get('genre', '')} · {cfg.get('style', '')} · {cfg.get('pov', '')}"

    if format == "txt":
        return _export_txt(title, meta, chapters)
    elif format == "html":
        return _export_html(title, meta, chapters)
    else:
        return _export_epub(title, meta, chapters)


def _export_txt(title: str, meta: str, chapters: list):
    buf = io.StringIO()
    buf.write(f"{title}\n{meta}\n")
    buf.write("=" * 50 + "\n\n")
    for ch in chapters:
        buf.write(f"第{ch['chapter_number']}章  {ch.get('title', '')}\n")
        buf.write("-" * 30 + "\n")
        buf.write((ch.get("content") or "") + "\n\n")
    buf.seek(0)

    filename = f"{title}.txt".encode("ascii", "ignore").decode()
    return StreamingResponse(
        iter([buf.read()]),
        media_type=TXT_MIMETYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _export_html(title: str, meta: str, chapters: list):
    safe_title = title.replace("&", "&amp;").replace("<", "&lt;")
    parts = [
        "<!DOCTYPE html><html lang='zh-CN'><head><meta charset='utf-8'>",
        f"<title>{safe_title}</title>",
        "<style>body{max-width:720px;margin:40px auto;font:16px/2 'Noto Serif SC',Georgia,serif;color:#2c2420;background:#fff}",
        "h1{text-align:center;font-size:24px;margin-bottom:4px}",
        ".meta{text-align:center;color:#888;font-size:13px;margin-bottom:32px}",
        "h2{font-size:18px;margin-top:32px;border-bottom:1px solid #ddd;padding-bottom:6px}",
        "p{text-indent:2em;margin:0 0 .8em}",
        "@media print{body{max-width:100%;margin:0;font-size:14px}}</style></head><body>",
        f"<h1>{safe_title}</h1>",
        f"<div class='meta'>{meta}</div>",
    ]
    for ch in chapters:
        parts.append(f"<h2>第{ch['chapter_number']}章  {ch.get('title', '')}</h2>")
        content = (ch.get("content") or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        for para in content.split("\n\n"):
            if para.strip():
                parts.append(f"<p>{para}</p>")
    parts.append("</body></html>")

    filename = f"{title}.html".encode("ascii", "ignore").decode()
    return StreamingResponse(
        iter(["".join(parts)]),
        media_type=HTML_MIMETYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _export_epub(title: str, meta: str, chapters: list):
    uid = str(uuid.uuid4())
    buf = io.BytesIO()

    opf_id = "book-id"
    opf = Element("package", {
        "xmlns": "http://www.id3.org/ns/id3",
        "version": "3.0",
        "unique-identifier": opf_id,
    })
    md = SubElement(opf, "metadata", {"xmlns:dc": "http://purl.org/dc/elements/1.1/"})
    SubElement(md, "dc:title").text = title
    SubElement(md, "dc:language").text = "zh-CN"
    SubElement(md, "dc:identifier", {"id": opf_id}).text = uid
    SubElement(md, "dc:creator").text = "AI Novelist"
    SubElement(md, "meta", {"name": "generator", "content": "AI Novelist"})

    manifest = SubElement(opf, "manifest")
    spine = SubElement(opf, "spine", {"toc": "ncx"})

    htmls: list[bytes] = []
    for ch in chapters:
        ch_id = f"ch{ch['chapter_number']}"
        safe_title = (ch.get("title") or "").replace("&", "&amp;").replace("<", "&lt;")
        content = (ch.get("content") or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        paras = "".join(f"<p>{p}</p>" for p in content.split("\n\n") if p.strip())

        html = (
            "<?xml version='1.0' encoding='utf-8'?>"
            "<!DOCTYPE html><html xmlns='http://www.w3.org/1999/xhtml' lang='zh-CN'><head>"
            f"<title>第{ch['chapter_number']}章</title></head><body>"
            f"<h2>第{ch['chapter_number']}章  {safe_title}</h2>{paras}</body></html>"
        ).encode("utf-8")

        htmls.append(html)
        SubElement(manifest, "item", {
            "id": ch_id, "href": f"{ch_id}.xhtml", "media-type": "application/xhtml+xml",
        })
        SubElement(spine, "itemref", {"idref": ch_id})

    SubElement(manifest, "item", {
        "id": "ncx", "href": "toc.ncx", "media-type": "application/x-dtbncx+xml",
    })

    opf_bytes = tostring(opf, encoding="utf-8", xml_declaration=True)

    ncx = Element("ncx", {
        "xmlns": "http://www.daisy.org/z3986/2005/ncx/", "version": "2005-1",
    })
    head = SubElement(ncx, "head")
    SubElement(head, "meta", {"name": "dtb:uid", "content": uid})
    SubElement(head, "meta", {"name": "dtb:depth", "content": "1"})
    SubElement(head, "meta", {"name": "dtb:totalPageCount", "content": "0"})
    SubElement(head, "meta", {"name": "dtb:maxPageNumber", "content": "0"})
    docTitle = SubElement(ncx, "docTitle")
    SubElement(docTitle, "text").text = title
    navMap = SubElement(ncx, "navMap")
    for i, ch in enumerate(chapters):
        np = SubElement(navMap, "navPoint", {"id": f"nav-ch{ch['chapter_number']}", "playOrder": str(i + 1)})
        SubElement(SubElement(np, "navLabel"), "text").text = f"第{ch['chapter_number']}章  {ch.get('title', '')}"
        SubElement(np, "content", {"src": f"ch{ch['chapter_number']}.xhtml"})

    ncx_bytes = tostring(ncx, encoding="utf-8", xml_declaration=True)

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mimetype", "application/epub+zip", zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">'
            '<rootfiles><rootfile full-path="content.opf" media-type="application/oebps-package+xml"/></rootfiles>'
            '</container>'
        ))
        zf.writestr("content.opf", opf_bytes)
        zf.writestr("toc.ncx", ncx_bytes)
        for i, ch in enumerate(chapters):
            zf.writestr(f"ch{ch['chapter_number']}.xhtml", htmls[i])

    buf.seek(0)
    filename = f"{title}.epub".encode("ascii", "ignore").decode()
    return StreamingResponse(
        iter([buf.read()]),
        media_type=EPUB_MIMETYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
