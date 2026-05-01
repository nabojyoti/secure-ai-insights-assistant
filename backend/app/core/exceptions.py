class AppError(Exception):
    status_code = 400
    code = "app_error"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class IngestionError(AppError):
    status_code = 422
    code = "ingestion_error"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class UnsafeQueryError(AppError):
    status_code = 400
    code = "unsafe_query"
