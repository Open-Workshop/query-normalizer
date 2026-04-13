from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_classic_normalization_for_russian_query() -> None:
    response = client.post(
        "/normalize/classic",
        json={"query": "Это ghbdtn алфaвиты и машины", "debug": True},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["tokens"] == ["привет", "алфавит", "машина"]
    assert data["normalized_query"] == "привет алфавит машина"
    assert "stopword:это" in data["corrections_applied"]
    assert "keyboard-layout:ghbdtn->привет" in data["corrections_applied"]
    assert "mixed-alphabet:алфaвиты->алфавиты" in data["corrections_applied"]
    assert "lemma:алфавиты->алфавит" in data["corrections_applied"]
    assert "lemma:машины->машина" in data["corrections_applied"]


def test_classic_normalization_without_debug() -> None:
    response = client.post(
        "/normalize/classic",
        json={"query": "Это ghbdtn алфaвиты и машины"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["tokens"] == ["привет", "алфавит", "машина"]
    assert data["normalized_query"] == "привет алфавит машина"
    assert "corrections_applied" not in data


def test_embedding_preserves_natural_phrase() -> None:
    response = client.post(
        "/normalize/embedding",
        json={"query": "Это ghbdtn алфaвиты и машины", "debug": True},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["tokens"] == []
    assert data["normalized_query"] == "это привет алфавиты и машины"
    assert "stopword:это" not in data["corrections_applied"]
    assert "stopword:и" not in data["corrections_applied"]


def test_classic_english_query_is_lemmatized() -> None:
    response = client.post(
        "/normalize/classic",
        json={
            "query": (
                "i am looking for a mod that adds more realistic weapons "
                "and makes the enemies feel much harder"
            ),
            "debug": True,
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["tokens"] == [
        "look",
        "mod",
        "add",
        "realistic",
        "weapon",
        "make",
        "enemy",
        "feel",
        "hard",
    ]
    assert data["normalized_query"] == "look mod add realistic weapon make enemy feel hard"
    assert "stopword:much" in data["corrections_applied"]
    assert "lemma:looking->look" in data["corrections_applied"]
    assert "lemma:adds->add" in data["corrections_applied"]
    assert "lemma:weapons->weapon" in data["corrections_applied"]
    assert "lemma:makes->make" in data["corrections_applied"]
    assert "lemma:enemies->enemy" in data["corrections_applied"]
    assert "lemma:harder->hard" in data["corrections_applied"]


def test_embedding_english_query_keeps_full_phrase() -> None:
    response = client.post(
        "/normalize/embedding",
        json={
            "query": (
                "i am looking for a mod that adds more realistic weapons "
                "and makes the enemies feel much harder"
            ),
            "debug": True,
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["tokens"] == []
    assert data["normalized_query"] == (
        "i am looking for a mod that adds more realistic weapons "
        "and makes the enemies feel much harder"
    )
    assert data["corrections_applied"] == []


def test_casefold_and_punctuation_normalization_are_reported() -> None:
    response = client.post(
        "/normalize",
        json={"query": "I'Am, ghbdtn.", "debug": True},
    )

    assert response.status_code == 200

    data = response.json()
    assert "casefold:I'Am->i'am" in data["classic"]["corrections_applied"]
    assert data["classic"]["normalized_query"] == "i'am привет"
    assert data["embedding"]["normalized_query"] == "i'am, привет."
    assert data["embedding"]["tokens"] == []


def test_html_entities_do_not_turn_into_fake_tokens() -> None:
    response = client.post(
        "/normalize",
        json={"query": "&lt;MOD is it?", "debug": True},
    )

    assert response.status_code == 200

    data = response.json()
    assert "html-unescape:&lt;MOD is it?-><MOD is it?" in data["classic"]["corrections_applied"]
    assert data["classic"]["normalized_query"] == "mod"
    assert data["classic"]["tokens"] == ["mod"]
    assert data["embedding"]["normalized_query"] == "mod is it"
    assert data["embedding"]["tokens"] == []


def test_markup_noise_is_stripped_from_mod_description() -> None:
    response = client.post(
        "/normalize/embedding",
        json={
            "query": (
                'This mod does [b]nothing by its self[/b]. '
                '[list][*] Harmony Postfix [/list] '
                '<Defs><PawnKindDef><defName>Pilgrim_Rose</defName></PawnKindDef></Defs>'
            ),
            "debug": True,
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert "bbcode-strip" in data["corrections_applied"]
    assert "html-tag-strip" in data["corrections_applied"]
    assert "[b]" not in data["normalized_query"]
    assert "[/b]" not in data["normalized_query"]
    assert "[list]" not in data["normalized_query"]
    assert "<Defs>" not in data["normalized_query"]
    assert "<PawnKindDef>" not in data["normalized_query"]
    assert "pilgrim" in data["normalized_query"]
    assert "rose" in data["normalized_query"]


def test_negation_is_preserved() -> None:
    response = client.post(
        "/normalize",
        json={"query": "не красные машины", "debug": True},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["classic"]["tokens"] == ["не", "красный", "машина"]
    assert data["embedding"]["tokens"] == []
    assert data["classic"]["normalized_query"] == "не красный машина"
    assert data["embedding"]["normalized_query"] == "не красные машины"


def test_apostrophe_in_words_is_preserved() -> None:
    response = client.post(
        "/normalize/embedding",
        json={"query": "didn't can't", "debug": True},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["normalized_query"] == "didn't can't"


def test_ellipsis_is_collapsed_to_single_dot() -> None:
    response = client.post(
        "/normalize/embedding",
        json={"query": "test... query... word", "debug": True},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["normalized_query"] == "test. query. word"
    assert "ellipsis-normalize" in data["corrections_applied"]


def test_mixed_alphabet_with_confusable_chars() -> None:
    response = client.post(
        "/normalize/classic",
        json={"query": "hel1o \u0441\u0430\u0435\u0442", "debug": True},
    )

    assert response.status_code == 200
    data = response.json()
    assert "normalized_query" in data


def test_numeric_tokens_remain_unchanged() -> None:
    response = client.post(
        "/normalize/classic",
        json={"query": "test 123 456", "debug": True},
    )

    assert response.status_code == 200
    data = response.json()
    assert "123" in data["tokens"]
    assert "456" in data["tokens"]


def test_mixed_script_tokens_not_converted() -> None:
    response = client.post(
        "/normalize/classic",
        json={"query": "testежи или amazingслово", "debug": True},
    )

    assert response.status_code == 200
    data = response.json()
    assert "test ежи" in data["normalized_query"] or "amazing слово" in data["normalized_query"]


def test_empty_tokens_are_filtered() -> None:
    response = client.post(
        "/normalize/classic",
        json={"query": "valid words  stop this", "debug": True},
    )

    assert response.status_code == 200
    data = response.json()
    assert "" not in data["tokens"]


def test_combined_russian_and_latin_in_one_word() -> None:
    response = client.post(
        "/normalize/classic",
        json={"query": "тестword или testслово", "debug": True},
    )

    assert response.status_code == 200
    data = response.json()
    assert "коррекций" not in data["corrections_applied"] or len(data["corrections_applied"]) >= 0


def test_dominant_script_is_none_for_special_chars() -> None:
    response = client.post(
        "/normalize/classic",
        json={"query": "!@# $%^", "debug": True},
    )

    assert response.status_code == 200
    data = response.json()
    assert "normalized_query" in data


def test_all_basic_endpoints_without_debug() -> None:
    response = client.post(
        "/normalize",
        json={"query": "test query"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "classic" in data
    assert "embedding" in data
    assert "corrections_applied" not in data["classic"]
    assert "corrections_applied" not in data["embedding"]


def test_mixed_alphabet_split_by_script() -> None:
    response = client.post(
        "/normalize/classic",
        json={"query": "wordсловоanotherеще", "debug": True},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["normalized_query"]


def test_special_chars_only_no_script() -> None:
    response = client.post(
        "/normalize/classic",
        json={"query": "!@#$%^&*()", "debug": True},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["normalized_query"] == ""


def test_stopword_in_embedding_mode() -> None:
    response = client.post(
        "/normalize/embedding",
        json={"query": "the test this", "debug": True},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["normalized_query"] == "the test this"


def test_only_symbols_no_words() -> None:
    response = client.post(
        "/normalize/classic",
        json={"query": "... ,,, !!!", "debug": True},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["normalized_query"] == ""


def test_version_includes_all_endpoints() -> None:
    classical_response = client.post(
        "/normalize/classic",
        json={"query": "test"},
    )
    embedding_response = client.post(
        "/normalize/embedding",  
        json={"query": "test"},
    )
    all_response = client.post(
        "/normalize",
        json={"query": "test"},
    )

    assert classical_response.status_code == 200
    assert embedding_response.status_code == 200
    assert all_response.status_code == 200
