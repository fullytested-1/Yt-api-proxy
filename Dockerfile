FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    ffmpeg curl git nodejs npm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# POT provider server clone + build
RUN git clone --depth 1 https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git /pot && \
    cd /pot/server && \
    npm install && \
    npx tsc

COPY . .

RUN chmod +x start.sh

EXPOSE 8000

CMD ["./start.sh"]
