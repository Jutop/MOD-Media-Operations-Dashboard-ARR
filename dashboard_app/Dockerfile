FROM python:3.12-alpine

WORKDIR /app

RUN apk add --no-cache docker-cli

COPY server.py /app/server.py
COPY core /app/core
COPY static /app/static

EXPOSE 8081

CMD ["python", "/app/server.py"]
