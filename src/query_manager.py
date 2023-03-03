import json.decoder

import pydantic
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session

from .database import Base


class PaginationQueryParams(BaseModel):
    page: int | None
    items_per_page: int | None


def pagination_params(
    page: int | None = None, items_per_page: int | None = None
) -> PaginationQueryParams:
    try:
        return PaginationQueryParams(page=page, items_per_page=items_per_page)
    except pydantic.error_wrappers.ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors()
        )


class SortingQueryParams(BaseModel):
    sort: str | None


def sorting_params(sort: str | None = None) -> SortingQueryParams:
    try:
        return SortingQueryParams(sort=sort)
    except pydantic.error_wrappers.ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors()
        )


class FilteringQueryParams(BaseModel):
    filters: dict

    @validator("filters", pre=True)
    def validate(cls, value) -> BaseModel:
        try:
            return json.loads(value)
        except json.decoder.JSONDecodeError:
            raise ValueError("Value is not a valid dict")


def filtering_params(filters: str | None = None) -> FilteringQueryParams:
    try:
        return FilteringQueryParams(filters=filters)
    except pydantic.error_wrappers.ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors()
        )


class CommonQueryParams:
    def __init__(
        self,
        pagination_query_params: PaginationQueryParams = Depends(pagination_params),
        sorting_query_params: SortingQueryParams = Depends(sorting_params),
        filtering_query_params: FilteringQueryParams = Depends(filtering_params),
    ):
        self.pagination_query_params = pagination_query_params
        self.sorting_query_params = sorting_query_params
        self.filtering_query_params = filtering_query_params

    def __repr__(self):
        return (
            f"{self.pagination_query_params}, "
            f"{self.sorting_query_params}, "
            f"{self.filtering_query_params} "
        )


class ParametrizedQuery:
    def __init__(self, db: Session, resource: Base, params: CommonQueryParams) -> None:
        self._db = db
        self._resource = resource
        self._query = db.query(resource)
        self._sort_by = []
        self._current_page = None
        self._items_per_page = None

        self._parse_params(params)
        self._assemble()

    def _parse_params(self, params) -> None:
        # filtering
        self.filters = params.filtering_query_params.filters

        # pagination
        self._current_page = params.pagination_query_params.page
        self._items_per_page = params.pagination_query_params.items_per_page

        # sorting
        columns = params.sorting_query_params.sort.split(",")
        for column in columns:
            name, order = column.split(":")
            self._sort_by.append(f"{name} {order}")

    def _filter(self) -> None:
        for column, values in self.filters.items():
            try:
                # todo: complete implementation
                self._query.where(getattr(self._resource, column).in_(values))
            except AttributeError:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    def _sort(self) -> None:
        self._query.order_by("".join(self._sort_by))

    def _paginate(self) -> None:
        self._query.limit(self._items_per_page)
        self._query.offset((self._current_page - 1) * self._items_per_page)

    def _assemble(self) -> None:
        self._filter()
        self._paginate()
        self._sort()

    def execute(self) -> list[Base]:
        return self._query.all()
