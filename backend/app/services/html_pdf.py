"""HTML 转 PDF（与申请模板排版一致）。"""

from io import BytesIO


def html_to_pdf_bytes(html: str) -> bytes:
    from xhtml2pdf import pisa

    buffer = BytesIO()
    status = pisa.CreatePDF(html, dest=buffer, encoding="utf-8")
    if status.err:
        raise RuntimeError("pdf render failed")
    return buffer.getvalue()
