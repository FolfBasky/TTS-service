import asyncio
import sys
from pathlib import Path

from parser import parse_docx
from formatter import prepare_tts_text, make_filename
from tts_engine import text_to_speech


async def process_topic(num, title, body, output_dir):
    filename = make_filename(num, title)
    tts_title = prepare_tts_text(title)
    tts_body = prepare_tts_text(body)

    full_text = f'{tts_title}. {tts_body}'

    output_path = output_dir / f'{filename}.mp3'
    print(f'  [{num}] {filename}.mp3')

    ok = await text_to_speech(full_text, output_path)
    if ok:
        print(f'    OK')
    else:
        print(f'    ERROR: не удалось озвучить')
        return False
    return True


async def main():
    if len(sys.argv) < 2:
        print('Использование: python main.py <путь_к_docx> [папка_вывода]')
        sys.exit(1)

    docx_path = Path(sys.argv[1])
    if not docx_path.exists():
        print(f'Файл не найден: {docx_path}')
        sys.exit(1)

    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('output')
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f'Парсинг: {docx_path}')
    topics = parse_docx(str(docx_path))
    print(f'Найдено тем: {len(topics)}\n')

    success = 0
    for num, title, body in topics:
        ok = await process_topic(num, title, body, output_dir)
        if ok:
            success += 1

    print(f'\nГотово: {success}/{len(topics)} тем сохранено в {output_dir}')


if __name__ == '__main__':
    asyncio.run(main())
