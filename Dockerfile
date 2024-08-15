# Используем новый облегченный образ Python
FROM python:3.12-alpine

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем файл requirements.txt в рабочую директорию
COPY requirements.txt .

# Устанавливаем зависимости из requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы приложения в рабочую директорию
COPY . .

# Указываем команду для запуска приложения
CMD ["python", "main.py", "--setup", "setup"]