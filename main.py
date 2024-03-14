import os
import re
import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
from dotenv import load_dotenv
from views import read_xml_files, save_data_to_json, import_data_from_json

load_dotenv()

# Получить значения для доступа на почту
email_address = os.getenv('LOGIN')
password = os.getenv('PASSWORD')



target_senders = ["testazbak@gmail.com", "azrtestnar@gmail.com",
                  "deveyevd@gmail.com", "azrtestnar@gmail.com", "gulievalea@gmail.com"]

mail = imaplib.IMAP4_SSL("imap.gmail.com")
mail.login(email_address, password)

mail.select("inbox")

# Установка желаемой даты

desired_date = datetime(2024, 3, 14)  # Укажите дату когда пришло письмо (год, месяц, день)
process_date = datetime(2024, 2, 26)  # Укажите дату которую хотите обработать (год, месяц, день)

# Определение временного интервала за указанную дату
start_date = desired_date.strftime("%d-%b-%Y")
end_date = (desired_date + timedelta(days=1)).strftime("%d-%b-%Y")

process_start_date = process_date.strftime("%d-%b-%Y")
process_end_date = (desired_date + timedelta(days=1)).strftime("%d-%b-%Y")

print(start_date, end_date)

for target_sender in target_senders:
    search_query = f'(FROM "{target_sender}" SINCE {start_date} BEFORE {end_date})'
    status, messages = mail.search(None, search_query)
    message_ids = messages[0].split()

    output_directory = "Reports"
    os.makedirs(output_directory, exist_ok=True)

    for message_id in message_ids:
        status, msg_data = mail.fetch(message_id, "(RFC822)")
        raw_email = msg_data[0][1]
        email_message = email.message_from_bytes(raw_email)
        subject, encoding = decode_header(email_message["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8")

        print(f"Обрабатывается письмо с темой: {subject}")

        match = re.search(r'(?ium)([a-z]{2,}) (\d{1,})', subject)
        if match:
            name, number = match.groups()
            name = name.capitalize()
            subdirectory = os.path.join(output_directory, f"{name} {start_date}")
            os.makedirs(subdirectory, exist_ok=True)

            subdirectorysms = os.path.join(subdirectory, "SMS")
            subdirectorycalls = os.path.join(subdirectory, "Calls")
            os.makedirs(subdirectorysms, exist_ok=True)
            os.makedirs(subdirectorycalls, exist_ok=True)

            for part in email_message.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                if part.get('Content-Disposition') is None:
                    continue

                
                if part.get_filename():
                    print(part.get_filename())
                    if "sms" in part.get_filename():
                        filename = f"Phone {number} " + part.get_filename()
                        filepath = os.path.join(subdirectorysms, filename)
                    elif "calls" in part.get_filename():
                        filename = f"Phone {number} " + part.get_filename()
                        filepath = os.path.join(subdirectorycalls, filename)
                    elif "list" in part.get_filename():
                        filename = part.get_filename()
                        filepath = os.path.join(subdirectory, filename)
                    with open(filepath, 'wb') as f:
                        f.write(part.get_payload(decode=True))
                    print(f"Вложение сохранено: {filename}")

mail.logout()


def str_to_timestamp(date_str):
    # Преобразование строки в объект datetime
    date_obj = datetime.strptime(date_str, "%d-%b-%Y")
    # Преобразование объекта datetime в Unix timestamp
    return int(date_obj.timestamp())

start_timestamp = str_to_timestamp(process_start_date) * 1000
end_timestamp = str_to_timestamp(process_end_date) * 1000

data = read_xml_files(xml_files_folder=f"{subdirectory}/SMS", folder_path=f"{subdirectory}", start_date=start_timestamp, end_date=end_timestamp)
save_data_to_json(data=data, folder_path=subdirectory)
import_data_from_json(folder_path=subdirectory)