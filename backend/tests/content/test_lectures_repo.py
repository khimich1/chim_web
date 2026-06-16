from app.repositories.content.lectures import LectureContentRepo


def test_list_topics_order_by_min_rowid(lectures_db) -> None:
    repo = LectureContentRepo(lectures_db)
    topics = repo.list_topics()

    assert [t.topic for t in topics] == ["Соли", "Алканы"]
    assert topics[0].chunk_count == 2
    assert topics[1].chunk_count == 1


def test_list_chunks_ordered_by_chunk_idx(lectures_db) -> None:
    repo = LectureContentRepo(lectures_db)
    chunks = repo.list_chunks("Соли")

    assert len(chunks) == 2
    assert chunks[0].chunk_idx == 0
    assert chunks[1].chunk_idx == 1
    assert chunks[0].has_audio is False
    assert chunks[1].has_audio is True
