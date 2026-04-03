# Usa uma imagem oficial e leve do Python
FROM python:3.12-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Evita que o Python grave arquivos .pyc e força o log a aparecer no terminal
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instala as dependências de sistema necessárias para o PostgreSQL
RUN apt-get update \
    && apt-get install -y gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instala os pacotes base do nosso stack (Django, Celery, Redis e o driver do Postgres)
RUN pip install --upgrade pip
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# Copia o resto do código do seu projeto para dentro do container
COPY . /app/