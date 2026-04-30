FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["fastapi", "dev", "./app/main.py", "--port", "8000", "--host", "0.0.0.0"]


# Билд
# docker build -t storage-system-back .

# Запуск на http://localhost:8000
# docker run -d -p 8000:8000 --name storage-system-back storage-system-back 

# Запущенные контейнеры
#docker ps

# Остановить контейнер
#docker stop storage-system-front

# Удалить контейнер
#docker rm storage-system-front

#=============================

# для сервака
# docker buildx build --platform linux/arm64 -t storage-system-back:arm64 --load ./
# docker save -o storage-system-back-arm64.tar storage-system-back:arm64
# scp -P 1409 storage-system-back-arm64.tar storage-system-front-arm64.tar ./app/db/storage.db ceziy@185.61.77.236:/home/ceziy/

# на сервере
# sudo docker load -i ~/storage-system-back-arm64.tar
# sudo docker load -i ~/storage-system-front-arm64.tar

# sudo docker network create storage-network


# sudo docker run -d --name storage-system-back --network storage-network -p 8000:8000 storage-system-back:arm64
# sudo docker cp ~/storage.db storage-system-back:/app/app/db/storage.db
# sudo docker restart storage-system-back


# sudo docker run -d --name storage-system-front --network storage-network -p 3000:80 storage-system-front:arm64



# зайти в контейнер
# sudo docker exec -it storage-system-back sh


#===========================
# удаление с сервера


# sudo docker stop storage-system-back storage-system-front

# sudo docker rm storage-system-back storage-system-front

# sudo docker rmi storage-system-back:arm64 storage-system-front:arm64

# sudo docker network rm storage-network

# rm -f ~/storage-system-back-arm64.tar ~/storage-system-front-arm64.tar ~/storage.db