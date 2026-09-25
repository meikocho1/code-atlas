from dataclasses import dataclass


@dataclass
class Expense:
    id: str
    amount: int
    status: str = "pending"


def submit_expense(expense: Expense) -> None:
    expense.status = "approved"
