import re
import docx
from docx.oxml.ns import qn
from lxml import etree

TOPIC_RE = re.compile(r'^(\d+)\.\s*(.*)')


def _paragraph_full_text(para):
    """Return paragraph text including OMML equation (m:t) content.

    python-docx's ``.text`` only reads ``w:t`` runs, skipping all
    ``m:t`` elements inside equations.  This helper extracts both.
    """
    parts = []
    # Iterate over all immediate children in document order, collecting
    # text from both w:t and m:t elements.
    for child in para._element.iter():
        tag = child.tag
        if tag == qn('w:t') and child.text:
            parts.append(child.text)
        elif tag == qn('m:t') and child.text:
            parts.append(child.text)
    return ''.join(parts)


def parse_docx(path):
    doc = docx.Document(path)
    paragraphs = [_paragraph_full_text(p).strip() for p in doc.paragraphs if _paragraph_full_text(p).strip()]

    topics = []
    current_num = None
    current_title = None
    current_body = []

    for line in paragraphs:
        m = TOPIC_RE.match(line)
        if m:
            if current_num is not None:
                topics.append((current_num, current_title, '\n'.join(current_body).strip()))
            current_num = int(m.group(1))
            current_title = m.group(2).rstrip('.')
            current_body = []
        else:
            if current_num is not None:
                current_body.append(line)

    if current_num is not None:
        topics.append((current_num, current_title, '\n'.join(current_body).strip()))

    return topics
