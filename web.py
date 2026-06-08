import os
import sys
import uuid
import shutil
import asyncio
import zipfile
import io
import traceback
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse, HTMLResponse, JSONResponse

from parser import parse_docx
from formatter import prepare_tts_text, make_filename
from tts_engine import text_to_speech

@asynccontextmanager
async def lifespan(app):
    TEMP_DIR.mkdir(exist_ok=True)
    yield
    shutil.rmtree(TEMP_DIR, ignore_errors=True)


app = FastAPI(title='Озвучка учебных тем', lifespan=lifespan)

BASE_DIR = Path(__file__).parent
TEMP_DIR = BASE_DIR / 'temp'
TEMP_DIR.mkdir(exist_ok=True)

tasks = {}


@app.exception_handler(Exception)
async def json_error(request: Request, exc: Exception):
    tb = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    print(f'ERROR [{request.method} {request.url.path}]: {exc}', file=sys.stderr)
    print(tb, file=sys.stderr)
    status = 500
    detail = str(exc) if str(exc) else 'Внутренняя ошибка сервера'
    if isinstance(exc, HTTPException):
        status = exc.status_code
        detail = exc.detail
    return JSONResponse(status_code=status, content={'error': detail})


@app.get('/', response_class=HTMLResponse)
async def index():
    path = BASE_DIR / 'templates' / 'index.html'
    return HTMLResponse(path.read_text(encoding='utf-8'))


@app.post('/upload')
async def upload(file: UploadFile = File(...)):
    print(f'UPLOAD: {file.filename}', file=sys.stderr)

    if not file.filename.endswith('.docx'):
        raise HTTPException(400, 'Только .docx файлы')

    task_id = str(uuid.uuid4())[:8]
    task_dir = TEMP_DIR / task_id
    task_dir.mkdir()

    docx_path = task_dir / 'input.docx'
    content = await file.read()
    docx_path.write_bytes(content)
    print(f'  saved to {docx_path} ({len(content)} bytes)', file=sys.stderr)

    try:
        topics = parse_docx(str(docx_path))
        print(f'  parsed: {len(topics)} topics', file=sys.stderr)
    except Exception as e:
        shutil.rmtree(task_dir)
        print(f'  parse error: {e}', file=sys.stderr)
        raise HTTPException(400, f'Ошибка парсинга: {e}')

    if not topics:
        shutil.rmtree(task_dir)
        raise HTTPException(400, 'Не найдено ни одной темы')

    tasks[task_id] = {
        'topics': topics,
        'dir': task_dir,
        'files': [],
        'done': False,
        'error': None,
    }

    try:
        asyncio.ensure_future(_process(task_id))
        print(f'  background task created: {task_id}', file=sys.stderr)
    except Exception as e:
        shutil.rmtree(task_dir)
        print(f'  task creation error: {e}', file=sys.stderr)
        raise HTTPException(500, f'Ошибка создания задачи: {e}')

    return {'task_id': task_id, 'total': len(topics)}


async def _process(task_id):
    info = tasks[task_id]
    topics = info['topics']
    out_dir = info['dir'] / 'mp3'
    out_dir.mkdir()

    try:
        for num, title, body in topics:
            filename = make_filename(num, title)
            tts_title = prepare_tts_text(title)
            tts_body = prepare_tts_text(body)
            full_text = f'{tts_title}. {tts_body}'

            output_path = out_dir / f'{filename}.mp3'
            ok = await text_to_speech(full_text, output_path)

            if ok:
                size = output_path.stat().st_size
                info['files'].append({
                    'name': f'{filename}.mp3',
                    'size': _fmt_size(size),
                    'path': str(output_path),
                })
    except Exception as e:
        info['error'] = str(e)

    info['done'] = True


def _fmt_size(size):
    if size < 1024:
        return f'{size} B'
    elif size < 1024 * 1024:
        return f'{size / 1024:.0f} KB'
    else:
        return f'{size / (1024 * 1024):.1f} MB'


@app.get('/status/{task_id}')
async def status(task_id: str):
    info = tasks.get(task_id)
    if not info:
        raise HTTPException(404, 'Задача не найдена')

    return {
        'done': info['done'],
        'total': len(info['topics']),
        'processed': len(info['files']),
        'files': info['files'],
        'error': info.get('error'),
    }


@app.get('/download/{task_id}/zip')
async def download_zip(task_id: str):
    info = tasks.get(task_id)
    if not info:
        raise HTTPException(404, 'Задача не найдена')

    mp3_dir = info['dir'] / 'mp3'
    if not mp3_dir.exists():
        raise HTTPException(404, 'Файлы не найдены')

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(mp3_dir.iterdir()):
            zf.write(str(f), arcname=f.name)
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type='application/zip',
        headers={'Content-Disposition': f'attachment; filename="topics_{task_id}.zip"'},
    )


@app.get('/download/{task_id}/{filename}')
async def download_file(task_id: str, filename: str):
    info = tasks.get(task_id)
    if not info:
        raise HTTPException(404, 'Задача не найдена')

    file_path = info['dir'] / 'mp3' / filename
    if not file_path.exists():
        raise HTTPException(404, 'Файл не найден')

    return FileResponse(str(file_path), media_type='audio/mpeg', filename=filename)


if __name__ == '__main__':
    import uvicorn
    import socket

    port = 8000
    while port < 8100:
        with socket.socket() as s:
            try:
                s.bind(('127.0.0.1', port))
                break
            except OSError:
                port += 1

    print(f'Сервер запущен: http://127.0.0.1:{port}', file=sys.stderr)
    uvicorn.run('web:app', host='127.0.0.1', port=port, reload=True)
