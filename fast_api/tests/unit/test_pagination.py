import pytest
from fast_api.validators.pagination import PaginationHelper


class TestValidatePagination:

    def test_validate_pagination_valid(self):
        skip, limit = PaginationHelper.validate_pagination(0, 50)
        assert skip == 0
        assert limit == 50

    def test_validate_pagination_large_skip(self):
        skip, limit = PaginationHelper.validate_pagination(1000, 50)
        assert skip == 1000
        assert limit == 50

    def test_validate_pagination_negative_skip_raises(self):
        with pytest.raises(ValueError, match="skip must be"):
            PaginationHelper.validate_pagination(-1, 50)

    def test_validate_pagination_zero_limit_raises(self):
        with pytest.raises(ValueError, match="limit must be"):
            PaginationHelper.validate_pagination(0, 0)

    def test_validate_pagination_negative_limit_raises(self):
        with pytest.raises(ValueError, match="limit must be"):
            PaginationHelper.validate_pagination(0, -1)

    def test_validate_pagination_limit_capped(self):
        skip, limit = PaginationHelper.validate_pagination(0, 5000)
        assert limit <= 100

    def test_validate_pagination_exact_max(self):
        skip, limit = PaginationHelper.validate_pagination(0, 100)
        assert limit == 100


class TestGetPaginationParams:

    def test_get_pagination_with_defaults(self):
        skip, limit = PaginationHelper.get_pagination_params()
        assert skip == 0
        assert limit == 50

    def test_get_pagination_custom_values(self):
        skip, limit = PaginationHelper.get_pagination_params(skip=10, limit=25)
        assert skip == 10
        assert limit == 25

    def test_get_pagination_none_values(self):
        skip, limit = PaginationHelper.get_pagination_params(skip=None, limit=None)
        assert skip == 0
        assert limit == 50

    def test_get_pagination_partial_none(self):
        skip, limit = PaginationHelper.get_pagination_params(skip=5, limit=None)
        assert skip == 5
        assert limit == 50


class TestCalculateOffset:

    def test_calculate_offset_page_1(self):
        offset = PaginationHelper.calculate_offset(1, 50)
        assert offset == 0

    def test_calculate_offset_page_2(self):
        offset = PaginationHelper.calculate_offset(2, 50)
        assert offset == 50

    def test_calculate_offset_page_5(self):
        offset = PaginationHelper.calculate_offset(5, 20)
        assert offset == 80

    def test_calculate_offset_page_10(self):
        offset = PaginationHelper.calculate_offset(10, 10)
        assert offset == 90

    def test_calculate_offset_negative_page_defaults_to_1(self):
        offset = PaginationHelper.calculate_offset(-1, 50)
        assert offset == 0

    def test_calculate_offset_zero_page_defaults_to_1(self):
        offset = PaginationHelper.calculate_offset(0, 50)
        assert offset == 0

    def test_calculate_offset_page_size_1(self):
        offset = PaginationHelper.calculate_offset(3, 1)
        assert offset == 2
