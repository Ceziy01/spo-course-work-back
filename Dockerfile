FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


# Билд
# docker build -t storage-system-back .

# Запуск на http://localhost:8000
# docker run -d -p 8000:8000 --name storage-system-back app

# Запущенные контейнеры
#docker ps

# Остановить контейнер
#docker stop storage-system-front

# Удалить контейнер
#docker rm storage-system-front