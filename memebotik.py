import os
import logging
from PIL import Image, ImageDraw, ImageFont
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен бота (замените на ваш)
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
CHANNEL_USERNAME = "@dragoncaneloni67"  # без @

# Создаем папку для временных файлов
if not os.path.exists('temp'):
    os.makedirs('temp')

# Инициализация бота
bot = telebot.TeleBot(BOT_TOKEN)

# Цвета рамок в RGB
FRAME_COLORS = {
    'purple': (128, 0, 128),
    'white': (255, 255, 255),
    'black': (0, 0, 0)
}

def check_subscription(user_id):
    """Проверяет, подписан ли пользователь на канал"""
    try:
        chat_member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return chat_member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Ошибка проверки подписки: {e}")
        return False

def create_image_with_frame(text, frame_color, user_id):
    """Создает изображение с текстом и рамкой"""
    try:
        # Размеры изображения
        width, height = 800, 600
        frame_width = 40
        
        # Создаем изображение
        image = Image.new('RGB', (width, height), color=frame_color)
        draw = ImageDraw.Draw(image)
        
        # Область для текста (внутри рамки)
        text_area = (frame_width, frame_width, width - frame_width, height - frame_width)
        
        # Загружаем шрифт (можно изменить путь к шрифту)
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except:
            font = ImageFont.load_default()
        
        # Разбиваем текст на строки
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            text_width = bbox[2] - bbox[0]
            
            if text_width <= (width - 2 * frame_width - 20):
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Рисуем текст
        y_position = (height - len(lines) * 50) // 2
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x_position = (width - text_width) // 2
            
            # Рисуем текст белым цветом для контраста
            text_color = (255, 255, 255) if frame_color == FRAME_COLORS['black'] else (0, 0, 0)
            draw.text((x_position, y_position), line, font=font, fill=text_color)
            y_position += 50
        
        # Сохраняем изображение
        filename = f"temp/image_{user_id}.jpg"
        image.save(filename, "JPEG")
        return filename
        
    except Exception as e:
        logger.error(f"Ошибка создания изображения: {e}")
        return None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    
    if not check_subscription(user_id):
        markup = InlineKeyboardMarkup()
        subscribe_button = InlineKeyboardButton("📢 Подписаться на канал", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")
        check_button = InlineKeyboardButton("✅ Проверить подписку", callback_data="check_subscription")
        markup.add(subscribe_button)
        markup.add(check_button)
        
        bot.send_message(
            message.chat.id,
            f"👋 Привет! Для использования бота необходимо подписаться на канал {CHANNEL_USERNAME}\n\n"
            "После подписки нажмите кнопку 'Проверить подписку'",
            reply_markup=markup
        )
    else:
        send_main_menu(message.chat.id)

def send_main_menu(chat_id):
    """Отправляет главное меню"""
    markup = InlineKeyboardMarkup()
    create_button = InlineKeyboardButton("🖼 Создать изображение", callback_data="create_image")
    markup.add(create_button)
    
    bot.send_message(
        chat_id,
        "🎉 Отлично! Вы подписаны на канал!\n\n"
        "Нажмите кнопку ниже, чтобы создать изображение с текстом и рамкой",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """Обработчик callback-запросов"""
    user_id = call.from_user.id
    
    if call.data == "check_subscription":
        if check_subscription(user_id):
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="✅ Отлично! Вы подписаны на канал!",
                reply_markup=None
            )
            send_main_menu(call.message.chat.id)
        else:
            bot.answer_callback_query(call.id, "❌ Вы еще не подписались на канал!")
    
    elif call.data == "create_image":
        if check_subscription(user_id):
            send_color_selection(call.message.chat.id)
        else:
            bot.answer_callback_query(call.id, "❌ Сначала подпишитесь на канал!")
    
    elif call.data in FRAME_COLORS.keys():
        if check_subscription(user_id):
            msg = bot.send_message(call.message.chat.id, "📝 Введите текст для изображения:")
            bot.register_next_step_handler(msg, process_text, call.data)
        else:
            bot.answer_callback_query(call.id, "❌ Сначала подпишитесь на канал!")

def send_color_selection(chat_id):
    """Отправляет меню выбора цвета рамки"""
    markup = InlineKeyboardMarkup()
    purple_button = InlineKeyboardButton("🟣 Фиолетовый", callback_data="purple")
    white_button = InlineKeyboardButton("⚪ Белый", callback_data="white")
    black_button = InlineKeyboardButton("⚫ Черный", callback_data="black")
    
    markup.add(purple_button)
    markup.add(white_button)
    markup.add(black_button)
    
    bot.send_message(
        chat_id,
        "🎨 Выберите цвет рамки:",
        reply_markup=markup
    )

def process_text(message, frame_color):
    """Обрабатывает текст и создает изображение"""
    user_id = message.from_user.id
    
    if not check_subscription(user_id):
        bot.send_message(message.chat.id, "❌ Для использования бота необходимо подписаться на канал!")
        return
    
    if len(message.text) > 500:
        bot.send_message(message.chat.id, "❌ Текст слишком длинный! Максимум 500 символов.")
        return
    
    # Показываем, что бот работает
    processing_msg = bot.send_message(message.chat.id, "⏳ Создаю изображение...")
    
    # Создаем изображение
    filename = create_image_with_frame(message.text, FRAME_COLORS[frame_color], user_id)
    
    if filename:
        # Отправляем изображение
        with open(filename, 'rb') as photo:
            color_name = {
                'purple': 'фиолетовой',
                'white': 'белой', 
                'black': 'черной'
            }[frame_color]
            
            bot.send_photo(
                message.chat.id,
                photo,
                caption=f"✅ Ваше изображение с {color_name} рамкой!\n\n"
                       f"Хотите создать еще одно? Используйте /start"
            )
        
        # Удаляем временный файл
        try:
            os.remove(filename)
        except:
            pass
    else:
        bot.send_message(message.chat.id, "❌ Произошла ошибка при создании изображения!")
    
    # Удаляем сообщение "Создаю изображение"
    try:
        bot.delete_message(message.chat.id, processing_msg.message_id)
    except:
        pass

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Обработчик всех сообщений"""
    user_id = message.from_user.id
    
    if not check_subscription(user_id):
        send_welcome(message)
    else:
        bot.send_message(
            message.chat.id,
            "👋 Используйте /start для начала работы с ботом!"
        )

if __name__ == "__main__":
    logger.info("Бот запущен...")
    bot.infinity_polling()
