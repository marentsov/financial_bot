from django.core.management.base import BaseCommand
import os
import sys
import django


class Command(BaseCommand):
    help = 'Запускает Telegram бота'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Запуск Telegram бота...'))

        # Убедимся что Django настроен
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        django.setup()

        try:
            from apps.bot.bot import bot
            bot.run()
        except ImportError as e:
            self.stderr.write(f"Ошибка импорта: {e}")
            self.stderr.write("Проверьте структуру проекта и импорты")
        except Exception as e:
            self.stderr.write(f"Ошибка запуска: {e}")
            import traceback
            traceback.print_exc()