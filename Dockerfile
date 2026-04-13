FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m nltk.downloader stopwords

COPY app ./app

EXPOSE 8000

CMD ["granian", "main:app", "--host", "0.0.0.0", "--port", "8000", "--interface", "asgi"]
