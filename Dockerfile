# Dockerfile для бота
FROM python:3.10-slim

# Установка зависимостей
WORKDIR /app

# Копируем файлы проекта
COPY . /app

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Команда запуска
CMD ["python", "-m", "your_package.main"]