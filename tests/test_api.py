from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_classic_normalization_for_russian_query() -> None:
    response = client.post(
        "/for/classic",
        json={"query": "Это ghbdtn алфaвиты и машины"},
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


def test_embedding_preserves_natural_phrase() -> None:
    response = client.post(
        "/for/embedding",
        json={"query": "Это ghbdtn алфaвиты и машины"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["tokens"] == ["это", "привет", "алфавиты", "и", "машины"]
    assert data["normalized_query"] == "это привет алфавиты и машины"
    assert "stopword:это" not in data["corrections_applied"]
    assert "stopword:и" not in data["corrections_applied"]


def test_classic_english_query_is_lemmatized() -> None:
    response = client.post(
        "/for/classic",
        json={
            "query": (
                "i am looking for a mod that adds more realistic weapons "
                "and makes the enemies feel much harder"
            )
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
        "/for/embedding",
        json={
            "query": (
                "i am looking for a mod that adds more realistic weapons "
                "and makes the enemies feel much harder"
            )
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["tokens"] == [
        "i",
        "am",
        "looking",
        "for",
        "a",
        "mod",
        "that",
        "adds",
        "more",
        "realistic",
        "weapons",
        "and",
        "makes",
        "the",
        "enemies",
        "feel",
        "much",
        "harder",
    ]
    assert data["normalized_query"] == (
        "i am looking for a mod that adds more realistic weapons "
        "and makes the enemies feel much harder"
    )
    assert data["corrections_applied"] == []


def test_casefold_and_punctuation_normalization_are_reported() -> None:
    response = client.post(
        "/for/all",
        json={"query": "I'Am, ghbdtn."},
    )

    assert response.status_code == 200

    data = response.json()
    assert "casefold:I'Am->i'am" in data["classic"]["corrections_applied"]
    assert "punctuation-normalize:i'am->i am" in data["classic"]["corrections_applied"]
    assert data["classic"]["normalized_query"] == "привет"
    assert data["embedding"]["normalized_query"] == "i am, привет."
    assert data["embedding"]["tokens"] == ["i", "am", ",", "привет", "."]


def test_html_entities_do_not_turn_into_fake_tokens() -> None:
    response = client.post(
        "/for/all",
        json={"query": "&lt;MOD is it?"},
    )

    assert response.status_code == 200

    data = response.json()
    assert "html-unescape:&lt;MOD is it?-><MOD is it?" in data["classic"]["corrections_applied"]
    assert data["classic"]["normalized_query"] == "mod"
    assert data["classic"]["tokens"] == ["mod"]
    assert data["embedding"]["normalized_query"] == "mod is it"
    assert data["embedding"]["tokens"] == ["mod", "is", "it"]


def test_markup_noise_is_stripped_from_mod_description() -> None:
    response = client.post(
        "/for/embedding",
        json={
            "query": (
                'This mod does [b]nothing by its self[/b]. '
                '[list][*] Harmony Postfix [/list] '
                '<Defs><PawnKindDef><defName>Pilgrim_Rose</defName></PawnKindDef></Defs>'
            )
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert "bbcode-strip" in data["corrections_applied"]
    assert "html-tag-strip" in data["corrections_applied"]
    assert "b" not in data["tokens"]
    assert "list" not in data["tokens"]
    assert "defs" not in data["tokens"]
    assert "pawnkinddef" not in data["tokens"]
    assert "defname" not in data["tokens"]
    assert "pilgrim" in data["tokens"]
    assert "rose" in data["tokens"]


def test_negation_is_preserved() -> None:
    response = client.post(
        "/for/all",
        json={"query": "не красные машины"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["classic"]["tokens"] == ["не", "красный", "машина"]
    assert data["embedding"]["tokens"] == ["не", "красные", "машины"]
