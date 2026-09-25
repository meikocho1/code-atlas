class ProjectPermissionError(Exception):
    pass


def delete_project(user_role: str, project_id: str) -> None:
    if user_role != "admin":
        raise ProjectPermissionError("only admins can delete projects")
    # delete logic omitted
