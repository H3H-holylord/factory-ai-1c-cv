import pytest
from src.db_1c import (
    Replica1CDatabase,
    ReadOnlyViolationError,
    AccessDeniedError,
    UserContext,
    answer_employee_question,
)


def test_readonly_replica_blocks_mutations_and_allows_select():
    db = Replica1CDatabase(":memory:")
    db.seed_synthetic_1c_data()

    rows = db.execute_readonly_query("SELECT shop, fact_qty, cv_qty FROM production_batches")
    assert len(rows) >= 4

    for forbidden_sql in [
        "DELETE FROM production_batches",
        "UPDATE production_batches SET fact_qty = 0",
        "DROP TABLE production_batches",
        "INSERT INTO production_batches VALUES (99, 'Литьё', 'Деталь', 10, 10, 10, '2026-11-02')",
    ]:
        with pytest.raises(ReadOnlyViolationError):
            db.execute_readonly_query(forbidden_sql)


def test_rbac_enforces_department_permissions_for_employees():
    db = Replica1CDatabase(":memory:")
    db.seed_synthetic_1c_data()

    director = UserContext(user_id=1, username="Иванов А.В. (Директор)", role="director")
    welder_master = UserContext(user_id=5, username="Петров С.Н. (Мастер цеха)", role="production")

    # Both can access production report
    prod_report = db.get_production_report(welder_master)
    assert len(prod_report) >= 2

    # Director can access procurement report, production master cannot
    proc_report = db.get_procurement_report(director)
    assert len(proc_report) >= 3

    with pytest.raises(AccessDeniedError):
        db.get_procurement_report(welder_master)


def test_local_ai_assistant_answers_1c_and_cv_questions():
    db = Replica1CDatabase(":memory:")
    db.seed_synthetic_1c_data()
    director = UserContext(user_id=1, username="Иванов А.В. (Директор)", role="director")

    reply = answer_employee_question(
        db=db,
        user=director,
        question="Сколько готовых деталей по литью и сварке зафиксировано камерами?",
    )
    assert "Литьё" in reply.answer
    assert "Сварка" in reply.answer
    assert "SELECT" in reply.generated_sql
