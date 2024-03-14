import os
import unicodedata
import xml.etree.ElementTree as ET
import chardet
import json
import math
from mysql.connector import Error
import mysql.connector
from models import Message
import openpyxl
from datetime import datetime


# Функция для чтения данных из файла .xlsx
def read_phone_numbers_from_xlsx(xlsx_folder):
    xlsx_files = [f for f in os.listdir(xlsx_folder) if f.endswith('.xlsx')]
    if not xlsx_files:
        raise FileNotFoundError(f"No .xlsx files found in '{xlsx_folder}'.")

    xlsx_file = os.path.join(xlsx_folder, xlsx_files[0])
    phone_numbers = {}
    wb = openpyxl.load_workbook(xlsx_file)
    ws = wb.active

    for row in ws.iter_rows(values_only=True):
        phone_id = str(row[0]).strip().lower()  # Приводим к нижнему регистру и удаляем лишние пробелы
        phone_number = str(row[1]).strip()
        phone_numbers[phone_id] = phone_number

    return phone_numbers

# Функция отвечающая за чтение данных из xml-файла
def read_xml_files(xml_files_folder, folder_path, start_date=None, end_date=None):
    try:
        phone_numbers = read_phone_numbers_from_xlsx(folder_path)
    except FileNotFoundError:
        print("Не найден файл")
        return []

    messages = []
    None_phone = []

    for filename in os.listdir(xml_files_folder):
        if filename.endswith('.xml'):
            xml_file = os.path.join(xml_files_folder, filename)
            tree = ET.parse(xml_file)
            root = tree.getroot()

            for sms_element in root.findall('sms'):
                body = sms_element.get('body')
                date = sms_element.get('date')
                address = sms_element.get('address')
                service_center = sms_element.get('service_center')
                contact_name = sms_element.get('contact_name')
                body_bytes = body.encode('utf-8')
                detected_encoding = detect_encoding(body_bytes)

                # Подсчет символов с учетом длины символов Unicode
                symbol_count = count_symbols(body)

                # Определение числа сегментов в сообщении
                segments = calculate_segments(detected_encoding, symbol_count)

                # # Проверяем, находится ли дата в пределах заданного диапазона
                if start_date and end_date:
                    if start_date <= int(date) <= end_date:
                        pass
                    else:
                        continue

                # Получение номера телефона из словаря по id
                phone_id = filename.split(' ')[1].strip().lower()  # Извлекаем id из названия файла
                phone_number = phone_numbers.get(f'phone {phone_id}')

                if phone_number is not None:
                    messages.append({
                        'date': date,  # Сохраняем числовую дату без изменений
                        'sender_id': address,
                        'phone_number': phone_number,
                        'service_center': service_center,
                        'sms_body': body,
                        'encoding': detected_encoding,
                        'segments': segments
                    })
                else:
                    None_phone.append(filename)
                    continue

    if None_phone:
        print(f"Наблюдается ошибка с этими файлами: {set(None_phone)}\nУстрани ошибку и попробуй снова!")

    return messages


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

def save_data_to_json(data, folder_path):
    with open(f'{folder_path}/data.json', 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)
    print(f"Все данные сохранены в 'data.json'.")
 

def import_data_from_json(folder_path, host, database, username, password):
    try:
        # Подключение к базе данных
        conn = mysql.connector.connect(
            host=host,
            database=database,
            user=username,
            password=password
        )
        if conn.is_connected():
            print('Connected to MySQL database')

            # Создание курсора для выполнения запросов
            cursor = conn.cursor()

            # Открытие файла JSON
            with open(f'{folder_path}/data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Вставка данных в базу данных
            for item in data:
                # Создание экземпляра модели и сохранение его в базе данных
                date = datetime.fromtimestamp(int(item['date']) / 1000)
                formatted_date_time = date.strftime("%Y-%m-%d %H:%M:%S") 
                obj = Message(
                    date=date,
                    sender_id=item['sender_id'],
                    phone_number=item['phone_number'],
                    service_center=item['service_center'],
                    sms_body=item['sms_body'],
                    encoding=item['encoding'],
                    segments=item['segments']
                )
                # Проверка существования данных в базе
                query = "SELECT COUNT(*) FROM MESSAGES WHERE date = %s AND sender_id = %s AND phone_number = %s AND service_center = %s AND sms_body = %s AND encoding = %s AND segments = %s"
                cursor.execute(query, (formatted_date_time, obj.sender_id, obj.phone_number, obj.service_center, obj.sms_body, obj.encoding, obj.segments))
                result = cursor.fetchone()
                count = result[0]

                if count == 0:
                    # Выполнение запроса INSERT для сохранения данных
                    query = "INSERT INTO MESSAGES (date, sender_id, phone_number, service_center, sms_body, encoding, segments) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                    cursor.execute(query, (obj.date, obj.sender_id, obj.phone_number, obj.service_center, obj.sms_body, obj.encoding, obj.segments))
                else:
                    print('Данные уже существуют, пропускаем вставку.')
                    
            # Подтверждение изменений
            conn.commit()

            print('Данные успешно импортированы.')

    except Error as e:
        print(f"Error while connecting to MySQL: {e}")

    finally:
        # Закрытие курсора и соединения
        if 'cursor' in locals() and cursor is not None:
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

    return {'error': 'Произошла ошибка при импорте данных в базу данных.'}


