# Етап 1: Базовий образ для збірки
FROM nvidia/cuda:12.1.0-devel-ubuntu22.04 as builder

# Встановлюємо необхідні залежності для збірки
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Встановлюємо необхідні Python пакети
WORKDIR /
COPY requirements_preprocess.txt .
RUN pip3 install --no-cache-dir -r requirements_preprocess.txt

# Етап 2: Фінальний образ
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

# Встановлюємо тільки необхідні пакети
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Копіюємо встановлені Python пакети
COPY --from=builder /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages

# Створюємо робочу директорію
WORKDIR /

# Копіюємо необхідні файли
COPY preprocess_handler.py .
COPY .env_prod .
COPY ckpts ./ckpts

# Створюємо користувача без прав root
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Встановлюємо змінні середовища
ENV PYTHONUNBUFFERED=1
ENV CUDA_VISIBLE_DEVICES=0

# Точка входу
CMD ["python3", "-u", "preprocess_handler.py"]