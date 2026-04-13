# Query Normalizer

Modern Python library for search-query normalization with bilingual support (Russian/English).

## Features

- **Text Cleaning**: Removes BBCode, HTML/XML tags, HTML entities
- **Keyboard Layout Fixing**: Automatically fixes mixed latin/cyrillic layouts
- **Mixed Script Detection**: Handles confusable characters and mixed alphabets
- **Lemmatization**: Converts words to base forms (classic mode)
- **Stopword Removal**: Filters out common words (classic mode)
- **Punctuation Preservation**: Keeps punctuation for embedding models
- **Dual Modes**: Optimized for classic search and embedding models

## Installation

```bash
pip install query-normalizer
```

Or with server support:

```bash
pip install query-normalizer[server]
```

## Library Usage

```python
from query_normalizer import QueryNormalizer

normalizer = QueryNormalizer()

# Classic mode: lemmatized, stopwords removed
result = normalizer.normalize_for_classic("Это ghbdtn алфaвиты и машины")
print(result.normalized_query)  # "привет алфавит машина"
print(result.tokens)  # ["привет", "алфавит", "машина"]

# Embedding mode: natural language preserved
result = normalizer.normalize_for_embedding("Это ghbdtn алфaвиты и машины")
print(result.normalized_query)  # "это привет алфавиты и машины"

# Debug mode shows all corrections
result = normalizer.normalize_for_classic("test query", debug=True)
for correction in result.corrections_applied:
    print(correction)
```

## CLI Usage

```bash
# Basic normalization
query-normalizer "Это ghbdtn алфaвиты и машины"

# Classic mode only
query-normalizer "test query" --mode classic

# Embedding mode only  
query-normalizer "test query" --mode embedding

# Show debug info
query-normalizer "test query" --debug
```

## Server Usage

```bash
# Install with server dependencies
pip install query-normalizer[server]

# Run FastAPI server
uvicorn query_normalizer.server:app --reload
```

API will be available at `http://127.0.0.1:8000`, Swagger UI at `http://127.0.0.1:8000/docs`

### API Endpoints

- `POST /normalize/classic` - Optimized for classic search (lemmatized, stopwords removed)
- `POST /normalize/embedding` - Optimized for embedding models (natural language preserved)
- `POST /normalize` - Both normalizations in one response
- `GET /health` - Health check

### Example Request

```bash
curl -X POST http://127.0.0.1:8000/normalize \
  -H 'Content-Type: application/json' \
  -d '{"query":"Это ghbdtn алфaвиты и машины", "debug": true}'
```

Example Response:

```json
{
  "classic": {
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
    "normalized_query": "это привет алфавиты и машины",
    "tokens": [],
    "corrections_applied": [
      "keyboard-layout:ghbdtn->привет",
      "mixed-alphabet:алфaвиты->алфавиты"
    ]
  }
}
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=query_normalizer --cov-report=term-missing

# Format code
ruff format .

# Lint code
ruff check .

# Type check
mypy query_normalizer/
```

## Dependencies

- `pymorphy3` - Russian lemmatization
- `simplemma` - English lemmatization  
- `nltk` - English stopwords
- `stop-words` - Russian stopwords
- `confusable-homoglyphs` - Mixed alphabet detection
- `beautifulsoup4` - HTML/XML parsing

## License

MIT License - see [LICENSE](LICENSE) for details.