from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from financial_bot.apps.bot.models import TelegramUser, ExpenseRequest
import logging

logger = logging.getLogger(__name__)


START_MENU = 0


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user

    # Сохраняем/обновляем пользователя
    tg_user, created = TelegramUser.objects.get_or_create(
        telegram_id=user.id,
        defaults={
            'username': user.username,
            'full_name': f"{user.first_name} {user.last_name or ''}".strip()
        }
    )

    if not created:
        tg_user.username = user.username
        tg_user.full_name = f"{user.first_name} {user.last_name or ''}".strip()
        tg_user.save()

    # Главное меню
    keyboard = [['Новая заявка', 'Мои заявки']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    welcome_text = (
        f"Привет, {user.first_name}!\n\n"
        "Я бот для подачи заявок на возмещение расходов.\n"
        "Выберите действие:"
    )

    await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    return START_MENU


async def my_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать мои заявки"""
    user = update.effective_user

    try:
        tg_user = TelegramUser.objects.get(telegram_id=user.id)
        requests = ExpenseRequest.objects.filter(user=tg_user).order_by('-created_at')[:5]

        if not requests:
            await update.message.reply_text("У вас пока нет заявок.")
            return START_MENU

        response = "📋 Ваши последние заявки:\n\n"
        for req in requests:
            status_emoji = {
                'new': '🆕',
                'approved': '✅',
                'rejected': '❌'
            }.get(req.status, '📄')

            response += (
                f"{status_emoji} Заявка #{req.id}\n"
                f"Сумма: {req.amount} руб.\n"
                f"Статус: {req.get_status_display()}\n"
                f"Дата: {req.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                f"{'-' * 30}\n"
            )

        await update.message.reply_text(response)
    except TelegramUser.DoesNotExist:
        await update.message.reply_text("Вы не зарегистрированы. Нажмите /start")

    return START_MENU


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = (
        "<b>Доступные команды:</b>\n\n"
        "/start - Главное меню\n"
        "/help - Эта справка\n\n"
        "<b>Как подать заявку:</b>\n"
        "1. Нажмите 'Новая заявка'\n"
        "2. Укажите сумму\n"
        "3. Напишите обоснование\n"
        "4. Прикрепите фото чека\n\n"
        "Статусы заявок:\n"
        "Новая - на рассмотрении\n"
        "Одобрена - одобрена финансистом\n"
        "Отклонена - отклонена с комментарием"
    )
    await update.message.reply_text(help_text, parse_mode='HTML')
    return START_MENU


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена текущего действия"""
    await update.message.reply_text(
        "Действие отменено.",
        reply_markup=ReplyKeyboardMarkup([['Новая заявка', 'Мои заявки']], resize_keyboard=True)
    )
    return START_MENU