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


def test_list_chunk_summaries_omits_lecture_text(lectures_db) -> None:
    repo = LectureContentRepo(lectures_db)
    summaries = repo.list_chunk_summaries("Соли")

    assert len(summaries) == 2
    assert summaries[0].chunk_title == "Введение"
    assert summaries[1].has_audio is True


def test_get_chunk_and_audio(lectures_db) -> None:
    repo = LectureContentRepo(lectures_db)

    chunk = repo.get_chunk("Соли", 1)
    assert chunk is not None
    assert chunk.lecture == "# Свойства солей"

    assert repo.get_audio("Соли", 1) == b"audio"
    assert repo.get_audio("Соли", 0) is None
    assert repo.get_chunk("Соли", 99) is None
