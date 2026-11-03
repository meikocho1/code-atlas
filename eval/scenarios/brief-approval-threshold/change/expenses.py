from dataclasses import dataclass

APPROVAL_THRESHOLD = 100_000


@dataclass
class Expense:
    id: str
    amount: int
    status: str = "pending"


def submit_expense(expense: Expense) -> None:
    if expense.amount > APPROVAL_THRESHOLD:
        expense.status = "awaiting_manager_approval"
    else:
        expense.status = "approved"


def approve_expense(expense: Expense) -> None:
    if expense.status != "awaiting_manager_approval":
        raise ValueError("only expenses awaiting approval can be approved")
    expense.status = "approved"
