# query-normalizer

FastAPI-микросервис для нормализации поисковых запросов в двух режимах:

- `POST /for/classic`:
  исправление раскладки, чистка смешанных алфавитов, удаление стоп-слов и лемматизация.
- `POST /for/embedding`:
  исправление раскладки и чистка смешанных алфавитов без удаления стоп-слов и без лемматизации; запятая и точка сохраняются.
- `POST /for/all`:
  оба варианта нормализации в одном ответе.

Дополнительно есть `GET /health`.

## Запуск

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Сервис будет доступен на `http://127.0.0.1:8000`, Swagger UI на `http://127.0.0.1:8000/docs`.

## Пример запроса

```bash
curl -X POST http://127.0.0.1:8000/for/all \
  -H 'Content-Type: application/json' \
  -d '{"query":"Это ghbdtn алфaвиты и машины"}'
```

Пример ответа:

```json
{
  "original_query": "Это ghbdtn алфaвиты и машины",
  "classic": {
    "original_query": "Это ghbdtn алфaвиты и машины",
    "normalized_query": "привет алфавит машина",
    "tokens": ["привет", "алфавит", "машина"],
    "corrections_applied": [
      "stopword:это",
      "keyboard-layout:ghbdtn->привет",
      "mixed-alphabet:алфaвиты->алфавиты",
      "lemma:алфавиты->алфавит",
      "lemma:машины->машина",
      "stopword:и"
    ]
  },
  "embedding": {
    "original_query": "Это ghbdtn алфaвиты и машины",
    "normalized_query": "это привет алфавиты и машины",
    "tokens": ["это", "привет", "алфавиты", "и", "машины"],
    "corrections_applied": [
      "keyboard-layout:ghbdtn->привет",
      "mixed-alphabet:алфaвиты->алфавиты"
    ]
  }
}
```

Пример для регистра и пунктуации:

```json
{
  "original_query": "I'Am, ghbdtn.",
  "classic": {
    "original_query": "I'Am, ghbdtn.",
    "normalized_query": "привет",
    "tokens": ["привет"],
    "corrections_applied": [
      "casefold:I'Am->i'am",
      "punctuation-normalize:i'am->i am",
      "stopword:i",
      "stopword:am",
      "keyboard-layout:ghbdtn->привет"
    ]
  },
  "embedding": {
    "original_query": "I'Am, ghbdtn.",
    "normalized_query": "i am, привет.",
    "tokens": ["i", "am", ",", "привет", "."],
    "corrections_applied": [
      "casefold:I'Am->i'am",
      "punctuation-normalize:i'am->i am",
      "keyboard-layout:ghbdtn->привет"
    ]
  }
}
```

## Библиотеки

В сервисе используются готовые решения там, где это практично:

- `pymorphy3` для русской лемматизации
- `simplemma` для английской лемматизации
- `nltk` для английских стоп-слов
- `stop-words` для русских стоп-слов
- `confusable-homoglyphs` для обнаружения смешанных алфавитов

## Тесты

```bash
pip install -r requirements-dev.txt
pytest
```
