import re
import docx

TOPIC_RE = re.compile(r'^(\d+)\.\s*(.*)')

def parse_docx(path):
    doc = docx.Document(path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

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
