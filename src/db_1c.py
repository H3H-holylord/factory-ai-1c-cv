from dataclasses import dataclass
import re
import sqlite3
from typing import Any, Dict, List


class ReadOnlyViolationError(PermissionError):
    """Raised when a query attempts to mutate the 1C Read-Only replica."""


class AccessDeniedError(PermissionError):
    """Raised when an employee's RBAC role lacks permission for a report."""


@dataclass(frozen=True)
class UserContext:
    user_id: int
    username: str
    role: str  # "director", "production", "procurement", "viewer"


@dataclass(frozen=True)
class AssistantReply:
    question: str
    generated_sql: str
    answer: str
    rows: List[Dict[str, Any]]


_FORBIDDEN_SQL_PATTERN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|TRUNCATE|ATTACH|DETACH|PRAGMA)\b",
    re.IGNORECASE,
)


def validate_readonly_sql(sql: str) -> str:
    cleaned = sql.strip().rstrip(";")
    if ";" in cleaned or not cleaned.upper().startswith("SELECT") or _FORBIDDEN_SQL_PATTERN.search(cleaned):
        raise ReadOnlyViolationError(f"Forbidden non-SELECT query on 1C Read-Only replica: {sql}")
    return cleaned


class Replica1CDatabase:
    """Read-Only replica of 1C:Enterprise data (Production, CV Counters, Procurement)."""

    def __init__(self, db_path: str = ":memory:"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def seed_synthetic_1c_data(self) -> None:
        cur = self.conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS production_batches (
                id INTEGER PRIMARY KEY,
                shop TEXT NOT NULL,
                part_name TEXT NOT NULL,
                plan_qty INTEGER NOT NULL,
                fact_qty INTEGER NOT NULL,
                cv_qty INTEGER NOT NULL,
                shift_date TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS procurement_orders (
                id INTEGER PRIMARY KEY,
                material TEXT NOT NULL,
                supplier TEXT NOT NULL,
                weight_tons REAL NOT NULL,
                amount_rub INTEGER NOT NULL,
                status TEXT NOT NULL,
                delivery_date TEXT NOT NULL
            );

            DELETE FROM production_batches;
            DELETE FROM procurement_orders;

            INSERT INTO production_batches (id, shop, part_name, plan_qty, fact_qty, cv_qty, shift_date) VALUES
                (1, 'Литьё (Линия №1)', 'Корпус редуктора ЧЛ-40', 450, 442, 442, '2026-11-02'),
                (2, 'Литьё (Линия №2)', 'Фланец стальной ФС-120', 800, 785, 784, '2026-11-02'),
                (3, 'Сварка (Пост №1)', 'Кронштейн рамы КР-08', 180, 174, 174, '2026-11-02'),
                (4, 'Сварка (Пост №2)', 'Балка опорная БО-24', 120, 118, 115, '2026-11-02'),
                (5, 'Металлообработка (ЧПУ)', 'Вал приводной ВП-16', 320, 319, 319, '2026-11-02');

            INSERT INTO procurement_orders (id, material, supplier, weight_tons, amount_rub, status, delivery_date) VALUES
                (1, 'Чугун литейный ПЛ-1', 'ООО «УралМетСнаб»', 18.5, 647500, 'На складе', '2026-10-30'),
                (2, 'Сталь листовая 09Г2С (12 мм)', 'АО «МеталлСервис»', 12.0, 912000, 'В пути', '2026-11-03'),
                (3, 'Проволока сварочная СВ-08Г2С', 'ООО «ТехСварка»', 1.4, 238000, 'Оплачено', '2026-11-04'),
                (4, 'СОЖ и резцы твердосплавные', 'ООО «ПромИнструмент»', 0.3, 184000, 'На складе', '2026-10-28');
            """
        )
        self.conn.commit()

    def execute_readonly_query(self, sql: str) -> List[Dict[str, Any]]:
        safe_sql = validate_readonly_sql(sql)
        cur = self.conn.execute(safe_sql)
        return [dict(row) for row in cur.fetchall()]

    def get_production_report(self, user: UserContext) -> List[Dict[str, Any]]:
        if user.role not in ("director", "production"):
            raise AccessDeniedError(f"Role '{user.role}' cannot access production reports")
        return self.execute_readonly_query(
            "SELECT shop, part_name, plan_qty, fact_qty, cv_qty, (fact_qty - cv_qty) AS discrepancy FROM production_batches"
        )

    def get_procurement_report(self, user: UserContext) -> List[Dict[str, Any]]:
        if user.role not in ("director", "procurement"):
            raise AccessDeniedError(f"Role '{user.role}' cannot access procurement reports")
        return self.execute_readonly_query(
            "SELECT material, supplier, weight_tons, amount_rub, status, delivery_date FROM procurement_orders"
        )


def answer_employee_question(
    db: Replica1CDatabase,
    user: UserContext,
    question: str,
) -> AssistantReply:
    q_lower = question.lower()
    if "закуп" in q_lower or "сырь" in q_lower or "постав" in q_lower:
        rows = db.get_procurement_report(user)
        sql = "SELECT material, supplier, weight_tons, amount_rub, status, delivery_date FROM procurement_orders"
        total_rub = sum(r["amount_rub"] for r in rows)
        lines = [
            f"• {r['material']} ({r['supplier']}): {r['weight_tons']} т — {r['amount_rub']:,} ₽ [{r['status']}]".replace(",", " ")
            for r in rows
        ]
        answer = (
            f"По данным Read-Only реплики 1С активны {len(rows)} заказа(ов) на общую сумму {total_rub:,} ₽:\n".replace(",", " ")
            + "\n".join(lines)
        )
        return AssistantReply(question=question, generated_sql=sql, answer=answer, rows=rows)

    rows = db.get_production_report(user)
    sql = "SELECT shop, part_name, plan_qty, fact_qty, cv_qty, (fact_qty - cv_qty) AS discrepancy FROM production_batches"
    total_cv = sum(r["cv_qty"] for r in rows)
    total_fact = sum(r["fact_qty"] for r in rows)
    lines = [
        f"• {r['shop']} ({r['part_name']}): 1С = {r['fact_qty']} шт. | Камера CV = {r['cv_qty']} шт."
        + (f" (расхождение: {r['discrepancy']} шт.)" if r["discrepancy"] != 0 else " (совпадает 100%)")
        for r in rows
    ]
    answer = (
        f"Сводка 1С + Компьютерное зрение за смену (всего по 1С: {total_fact} шт., по видеокамерам: {total_cv} шт.):\n"
        + "\n".join(lines)
    )
    return AssistantReply(question=question, generated_sql=sql, answer=answer, rows=rows)
