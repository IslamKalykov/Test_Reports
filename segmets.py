import unicodedata
import chardet
import math


text = 'Срок действия персонального предложения истек. Пакет для роуминга отключен. Теперь связь за границей оплачивается по условиям вашего тарифа. Узнать условия или подключить новое персональное предложение здесь:  https://mybee.page.link/roum_info'
text_bytes = text.encode('utf-8')


def detect_encoding(text_bytes):
    result = chardet.detect(text_bytes)
    return result['encoding']


def count_symbols(text):
    count = 0
    for char in text:
        if unicodedata.east_asian_width(char) in ('F', 'W'):
            count += 2
        else:
            count += 1
    return count


def calculate_segments(encoding, symbol_count):
    if encoding == 'ascii':
        return 1 if symbol_count <= 160 else math.ceil(symbol_count / 153)
    else:
        return 1 if symbol_count <= 70 else math.ceil(symbol_count / 67)


# То что нужно подставить в encoding
detected_encoding = detect_encoding(text_bytes)
print(detected_encoding)

# Подсчет символов с учетом длины символов Unicode
symbol_count = count_symbols(text)
print(symbol_count)

# Определение числа сегментов в сообщении

# То что нужно подставить в segments
segments = calculate_segments(detected_encoding, symbol_count)
print(segments)