from app.models.enums import ExamTrack
from app.repositories.content.tests import ExamContentRepo


def test_list_task_types_returns_distinct_types(ege_tests_db) -> None:
    repo = ExamContentRepo(ege_tests_db)
    assert repo.list_task_types() == [1, 2]


def test_list_variants_excludes_bug_and_has_issue(ege_tests_db) -> None:
    repo = ExamContentRepo(ege_tests_db)
    variants = repo.list_variants()

    assert variants == ["001.txt"]


def test_list_questions_filters_has_issue(ege_tests_db) -> None:
    repo = ExamContentRepo(ege_tests_db)
    questions = repo.list_questions("001.txt")

    assert len(questions) == 2
    assert [q.type for q in questions] == [1, 2]


def test_get_image_returns_blob(ege_tests_db) -> None:
    repo = ExamContentRepo(ege_tests_db)
    data = repo.get_image("рисунок0001.png")
    assert data == b"png-bytes"


def test_oge_repo_uses_separate_db(oge_tests_db, ege_tests_db) -> None:
    oge_variants = ExamContentRepo(oge_tests_db).list_variants()
    ege_variants = ExamContentRepo(ege_tests_db).list_variants()

    assert oge_variants == ["001.txt", "019.txt"]
    assert ege_variants == ["001.txt"]


def test_expand_types_across_variants_ege(ege_tests_db) -> None:
    repo = ExamContentRepo(ege_tests_db)
    sources = repo.expand_types_across_variants([1, 2], track=ExamTrack.EGE)

    assert sources == [
        ("001.txt", [1]),
        ("001.txt", [2]),
    ]
    assert repo.count_expanded_questions([1], track=ExamTrack.EGE) == 1


def test_expand_types_across_variants_oge(oge_tests_db) -> None:
    repo = ExamContentRepo(oge_tests_db)
    sources = repo.expand_types_across_variants([1], track=ExamTrack.OGE)

    assert sources == [("001.txt", None)]
    assert repo.count_expanded_questions([1], track=ExamTrack.OGE) == 1
