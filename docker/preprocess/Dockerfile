# Використовуємо PyTorch базовий образ
FROM pytorch/pytorch:2.6.0-cuda12.4-cudnn9-runtime

# Встановлюємо необхідні пакети
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Створюємо робочу директорію
WORKDIR /app

# Копіюємо файл з залежностями та встановлюємо їх
COPY requirements_preprocess.txt .
RUN pip3 install --no-cache-dir -r requirements_preprocess.txt

# Копіюємо необхідні файли
COPY preprocess_handler.py .
COPY .env_prod .
COPY ckpts ./ckpts
COPY test_input.json .

# Створюємо користувача без прав root та директорію
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Встановлюємо змінні середовища
ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=0

# Точка входу
CMD ["python3", "-u", "preprocess_handler.py"]