from django.core.management.base import BaseCommand
from financial_bot.apps.bot.bot import bot


class Command(BaseCommand):
    help = 'Запускает Telegram бота'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Запуск бота'))
        bot.run()