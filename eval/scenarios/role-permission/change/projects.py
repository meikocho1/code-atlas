class ProjectPermissionError(Exception):
    pass


ALLOWED_DELETE_ROLES = {"admin", "manager"}


def delete_project(user_role: str, project_id: str) -> None:
    if user_role not in ALLOWED_DELETE_ROLES:
        raise ProjectPermissionError("only admins or managers can delete projects")
    # delete logic omitted
