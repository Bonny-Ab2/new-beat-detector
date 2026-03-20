FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install cython numpy==1.20.3 && \
    pip install madmom==0.16.1 && \
    pip install git+https://github.com/mir-aidj/BeatNet.git && \
    pip install git+https://github.com/CPJKU/beat_this.git && \
    pip install -r requirements.txt

COPY app.py .
COPY app/ ./app/

EXPOSE 5000

CMD ["gunicorn", "-b", "0.0.0.0:5000", "-w", "2", "-t", "120", "app:app"]
