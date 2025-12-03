from django.core.management.base import BaseCommand
import os
import sys
import django


class Command(BaseCommand):
    help = 'Запускает Telegram бота'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Запуск Telegram бота...'))

        # Убедимся что Django настроен
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        django.setup()

        # Теперь импортируем бота
        try:
            # Попробуем оба варианта
            try:
                from apps.bot.bot import bot
                print("✅ Найден через apps.bot.bot")
            except ImportError:
                from bot.bot import bot
                print("✅ Найден через bot.bot")

            # Запускаем
            bot.run()

        except Exception as e:
            print(f"❌ Ошибка: {e}")
            print("\n📁 Проверка структуры:")

            # Проверим текущую директорию
            print(f"Текущая директория: {os.getcwd()}")

            # Проверим что есть в apps/bot
            if os.path.exists('apps/bot'):
                print("\napps/bot содержит:")
                for item in os.listdir('apps/bot'):
                    print(f"  - {item}")
                    if item == 'bot.py':
                        print(f"    Размер: {os.path.getsize('apps/bot/bot.py')} байт")