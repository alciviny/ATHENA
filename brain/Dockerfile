FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 1. Define o diretório de trabalho na raiz
WORKDIR /app

# 2. Instala dependências do SO
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 3. Copia e instala requirements (fica na raiz /app para cache)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 4. CRUCIAL: Copia o código para DENTRO de uma pasta 'brain' 
COPY . ./brain

# 5. Adiciona /app ao PYTHONPATH para o Python achar o módulo 'brain'
ENV PYTHONPATH=/app

EXPOSE 8000

# 6. Ajusta o comando para chamar 'brain.api...'
CMD ["uvicorn", "brain.api.fastapi.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "debug"]