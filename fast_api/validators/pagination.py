from __future__ import annotations

from fast_api.config import get_settings

settings = get_settings()


class PaginationHelper:

    @staticmethod
    def validate_pagination(skip: int = 0, limit: int = 50) -> tuple[int, int]:
        if skip < 0:
            raise ValueError("skip must be >= 0")
        if limit < 1:
            raise ValueError("limit must be >= 1")
        if limit > settings.PAGINATION_MAX_LIMIT:
            limit = settings.PAGINATION_MAX_LIMIT
        return skip, limit

    @staticmethod
    def get_pagination_params(
        skip: int | None = None, limit: int | None = None
    ) -> tuple[int, int]:
        skip = skip or 0
        limit = limit or settings.PAGINATION_DEFAULT_LIMIT
        return PaginationHelper.validate_pagination(skip, limit)

    @staticmethod
    def calculate_offset(page: int, page_size: int) -> int:
        if page < 1:
            page = 1
        return (page - 1) * page_size
