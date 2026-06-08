import string
import re

GREEK_MAP = {
    'α': 'альфа', 'Α': 'альфа',
    'β': 'бета', 'Β': 'бета',
    'γ': 'гамма', 'Γ': 'гамма',
    'δ': 'дельта', 'Δ': 'дельта',
    'ε': 'эпсилон', 'Ε': 'эпсилон',
    'ζ': 'дзета', 'Ζ': 'дзета',
    'η': 'эта', 'Η': 'эта',
    'θ': 'тэта', 'Θ': 'тэта',
    'ι': 'йота', 'Ι': 'йота',
    'κ': 'каппа', 'Κ': 'каппа',
    'λ': 'лямбда', 'Λ': 'лямбда',
    'μ': 'мю', 'Μ': 'мю',
    'ν': 'ню', 'Ν': 'ню',
    'ξ': 'кси', 'Ξ': 'кси',
    'ο': 'омикрон', 'Ο': 'омикрон',
    'π': 'пи', 'Π': 'пи',
    'ρ': 'ро', 'Ρ': 'ро',
    'σ': 'сигма', 'Σ': 'сигма',
    'τ': 'тау', 'Τ': 'тау',
    'υ': 'ипсилон', 'Υ': 'ипсилон',
    'φ': 'фи', 'Φ': 'фи',
    'χ': 'хи', 'Χ': 'хи',
    'ψ': 'пси', 'Ψ': 'пси',
    'ω': 'омега', 'Ω': 'омега',
}

SYMBOL_MAP = {
    '∞': 'бесконечность',
    '≠': 'не равно',
    '≤': 'меньше или равно',
    '≥': 'больше или равно',
    '⇒': 'следовательно',
    '⇔': 'равносильно',
    '≈': 'приблизительно',
    '∂': 'частная производная',
    '∛': 'корень кубический',
    '∈': 'принадлежит',
    '∉': 'не принадлежит',
    '⊂': 'подмножество',
    '⊃': 'надмножество',
    '∪': 'объединение',
    '∩': 'пересечение',
    '∀': 'для любого',
    '∃': 'существует',
    '∅': 'пустое множество',
    '±': 'плюс минус',
    '×': 'умножить',
    '÷': 'разделить',
    '∼': 'распределена как',
    '∝': 'пропорционально',
    '⊥': 'независимо',
}


def prepare_tts_text(text):
    text = text.strip()

    # 1. Function names
    for func, repl in [
        (r'\blim\b', 'лимит'),
        (r'\bsup\b', 'супремум'),
        (r'\binf\b', 'инфимум'),
        (r'\bmax\b', 'максимум'),
        (r'\bmin\b', 'минимум'),
        (r'\bargmin\b', 'арг минимум'),
        (r'\bargmax\b', 'арг максимум'),
        (r'\bsin\b', 'синус'),
        (r'\bcos\b', 'косинус'),
        (r'\btan\b', 'тангенс'),
        (r'\bcot\b', 'котангенс'),
        (r'\blog\b', 'логарифм'),
        (r'\bln\b', 'натуральный логарифм'),
        (r'\blg\b', 'десятичный логарифм'),
        (r'\bexp\b', 'экспонента'),
    ]:
        text = re.sub(func, repl, text)

    # 2. Statistical operators (must match before general symbol replacement)
    # M[content] - мат.ожидание
    text = re.sub(r'\bM\s*\[([^\]]*)\]', r' математическое ожидание от \1 ', text)
    # D[content] - дисперсия
    text = re.sub(r'\bD\s*\[([^\]]*)\]', r' дисперсия от \1 ', text)
    # Var(content)
    text = re.sub(r'\bVar\s*\(([^)]*)\)', r' дисперсия от \1 ', text)
    # Cov(content)
    text = re.sub(r'\bCov\s*\(([^)]*)\)', r' ковариация от \1 ', text)
    # Corr(content)
    text = re.sub(r'\bCorr\s*\(([^)]*)\)', r' корреляция от \1 ', text)
    # P(content) - вероятность
    text = re.sub(r'\bP\s*\(([^)]*)\)', r' вероятность \1 ', text)

    # 3. Greek letters
    for greek, repl in GREEK_MAP.items():
        text = text.replace(greek, f' {repl} ')

    # 4. Math symbols
    for sym, repl in SYMBOL_MAP.items():
        text = text.replace(sym, f' {repl} ')

    # 5. Single-symbol replacements
    for sym, repl in [
        ('∑', 'сумма'),
        ('∫', 'интеграл'),
        ('√', 'корень квадратный'),
        ('→', 'стремится к'),
        ('←', 'стремится к'),
        ('²', ' в квадрате'),
        ('³', ' в кубе'),
    ]:
        text = text.replace(sym, f' {repl} ')

    # 6. Combining diacritical marks (overline, hat, tilde)
    text = re.sub(r'(\w)\u0304', r' \1 с чертой ', text)
    text = re.sub(r'(\w)\u0305', r' \1 с чертой ', text)
    text = re.sub(r'(\w)\u0302', r' \1 с крышкой ', text)
    text = re.sub(r'(\w)\u0303', r' \1 с тильдой ', text)
    text = re.sub(r'(\w)\u0307', r' \1 с точкой ', text)

    # 7. Precomposed Unicode with diacritics
    for ch, repl in [
        ('Ā', 'A с чертой'), ('ā', 'а с чертой'),
        ('Ē', 'E с чертой'), ('ē', 'е с чертой'),
        ('Ī', 'I с чертой'), ('ī', 'и с чертой'),
        ('Ō', 'O с чертой'), ('ō', 'о с чертой'),
        ('Ū', 'U с чертой'), ('ū', 'у с чертой'),
        ('Ǣ', 'E с чертой'), ('ǣ', 'е с чертой'),
    ]:
        text = text.replace(ch, repl)

    # 8. Subscript patterns: X_n, X_{ij}
    text = re.sub(r'(\w)_{(\w+)}', r' \1 с индексами \2 ', text)
    text = re.sub(r'(\w)_(\w+)', r' \1 с индексом \2 ', text)
    text = text.replace('_', ' ')

    # 9. Superscript with braces: x^{2}
    text = re.sub(r'(\w)\^\{(.+?)\}', r' \1 в степени \2 ', text)
    text = re.sub(r'(\w)\^(\w)', r' \1 в степени \2 ', text)

    # 10. Fraction between single-letter variables or digits: a/b, 1/2
    text = re.sub(r'([a-zA-Z0-9])\s*/\s*([a-zA-Z0-9])', r' \1 разделить на \2 ', text)
    # Multiplication between single-letter variables or digits: a*b, 2*3
    text = re.sub(r'([a-zA-Z0-9])\s*\*\s*([a-zA-Z0-9])', r' \1 умножить на \2 ', text)

    # 11. Pipe for absolute value or conditional
    text = text.replace('|', ' модуль ')

    # 12. Clean up extra spaces
    text = re.sub(r'\s+', ' ', text)

    return text


def make_filename(num, title):
    text = f'{num}. {title}'
    for ch in string.punctuation:
        text = text.replace(ch, ' ')
    text = re.sub(r'\s+', '_', text.strip())
    text = text.strip('_')
    return text
