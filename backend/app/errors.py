class AppError(Exception):
    status_code = 500

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class InvalidURL(AppError):
    status_code = 422


class VideoNotFound(AppError):
    status_code = 404


class CommentsDisabled(AppError):
    status_code = 403


class RateLimited(AppError):
    status_code = 429


class UpstreamError(AppError):
    status_code = 502
