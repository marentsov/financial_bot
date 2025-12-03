FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Установка зависимостей Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование проекта
COPY . .

# Создание директорий для медиа и статики
RUN mkdir -p /app/media/receipts /app/staticfiles

# Настройка прав
RUN chmod +x /app/manage.py

# Порт для Django
EXPOSE 8000

# Команда запуска
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]