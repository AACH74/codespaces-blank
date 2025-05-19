import logging
import time
import os

import telebot
from openai import OpenAI
from PIL import Image
import pytesseract
import PyPDF2

# ——————————————————————————————
# Конфигурация
# ——————————————————————————————
TELEGRAM_TOKEN = "8154501881:AAEkuCRCZw91_hl7FNwSO-9QF3HRd_9nJHI"
OPENAI_API_KEY = "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"

bot = telebot.TeleBot(TELEGRAM_TOKEN)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# ——————————————————————————————
# Логирование
# ——————————————————————————————
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.INFO
)

# ——————————————————————————————
# Хранилище истории
# ——————————————————————————————
chat_histories: dict[int, list[dict]] = {}
HISTORY_LIMIT = 20

def get_ai_response(chat_id: int, user_text: str) -> str:
    history = chat_histories.setdefault(chat_id, [
        {"role": "system", "content":
         "Вы — дружелюбный и остроумный собеседник, умеющий поддержать любую тему."}
    ])
    history.append({"role": "user", "content": user_text})
    if len(history) > HISTORY_LIMIT:
        history[:] = history[:1] + history[-(HISTORY_LIMIT-1):]

    try:
        resp = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=history
        )
        ai_text = resp.choices[0].message.content.strip()
    except Exception:
        logging.exception("Ошибка при обращении к OpenAI")
        return "К сожалению, сервис сейчас недоступен. Попробуйте позже."

    history.append({"role": "assistant", "content": ai_text})
    return ai_text

# ——————————————————————————————
# OCR: Распознаём текст на отправленной фотографии
# ——————————————————————————————
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    # берём самую крупную версию фото
    file_id = message.photo[-1].file_id
    file_info = bot.get_file(file_id)
    img_bytes = bot.download_file(file_info.file_path)
    tmp_path = f"tmp_{file_id}.jpg"
    with open(tmp_path, 'wb') as f:
        f.write(img_bytes)

    try:
        text = pytesseract.image_to_string(Image.open(tmp_path), lang='rus+eng')
        if not text.strip():
            text = "(текст не распознан)"
    except Exception:
        logging.exception("Ошибка OCR")
        text = "Не удалось распознать текст на изображении."

    os.remove(tmp_path)
    bot.send_message(chat_id, f"Распознанный текст:\n{text}")

# ——————————————————————————————
# Работа с документами: txt и pdf
# ——————————————————————————————
@bot.message_handler(content_types=['document'])
def handle_document(message):
    chat_id = message.chat.id
    doc = message.document
    file_info = bot.get_file(doc.file_id)
    data = bot.download_file(file_info.file_path)
    filename = doc.file_name
    with open(filename, 'wb') as f:
        f.write(data)

    ext = filename.split('.')[-1].lower()
    result = ""
    try:
        if ext == 'txt':
            with open(filename, 'r', encoding='utf-8') as f:
                result = f.read()
        elif ext == 'pdf':
            reader = PyPDF2.PdfReader(filename)
            for page in reader.pages:
                result += page.extract_text() or ''
        else:
            result = f"Файл {filename} сохранён, но не распознан."
    except Exception:
        logging.exception("Ошибка при чтении файла")
        result = f"Ошибка при обработке {filename}."

    bot.send_message(chat_id, f"Результат обработки {filename}:\n{result}")
    # по желанию можно удалить файл после обработки
    os.remove(filename)

# ——————————————————————————————
# Текстовый чат: всё остальное шлём в AI
# ——————————————————————————————
@bot.message_handler(func=lambda m: m.text is not None)
def handle_text(message):
    chat_id = message.chat.id
    reply = get_ai_response(chat_id, message.text.strip())
    bot.send_message(chat_id, reply)

if __name__ == "__main__":
    logging.info("Бот запускается...")
    bot.polling(none_stop=True, interval=3, timeout=60)
