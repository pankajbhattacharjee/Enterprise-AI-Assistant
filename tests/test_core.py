from agents.sql_agent import validate_select
from rag.splitter import split_text
from rag.vectorstore import LocalVectorStore


def test_select_validation_rejects_writes():
    assert "LIMIT" in validate_select("SELECT * FROM sales")
    for query in ("DELETE FROM sales", "SELECT * FROM sales; DROP TABLE sales", "UPDATE sales SET amount = 0"):
        try: validate_select(query)
        except ValueError: pass
        else: raise AssertionError("unsafe query was accepted")


def test_splitter_preserves_words():
    chunks = split_text("one two three four five", chunk_size=3, overlap=1)
    assert chunks == ["one two three", "three four five"]


def test_local_vector_store_search_is_scoped(tmp_path, monkeypatch):
    monkeypatch.setattr("rag.vectorstore.get_settings", lambda: type("S", (), {"index_dir": tmp_path})())
    store = LocalVectorStore(); store.add([{"owner_id": 1, "document": "policy.txt", "text": "refunds are available within thirty days"}, {"owner_id": 2, "document": "other.txt", "text": "private data"}])
    assert store.search("refund policy", owner_id=1)[0]["document"] == "policy.txt"
    assert not store.search("private", owner_id=1)
