import pydantic
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session


class PaginationQueryParams(BaseModel):
    page: int | None = None
    items_per_page: int | None = None


def pagination_params(page: int | None = None,
                      items_per_page: int | None = None) -> PaginationQueryParams:
    try:
        return PaginationQueryParams(page=page, items_per_page=items_per_page)
    except pydantic.error_wrappers.ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=e.errors())


class SortingQueryParams(BaseModel):
    sort: str | None = None


def sorting_params(sort: str | None = None) -> SortingQueryParams:
    try:
        return SortingQueryParams(sort=sort)
    except pydantic.error_wrappers.ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=e.errors())


class CommonQueryParams:
    def __init__(self, pagination_query_params: PaginationQueryParams = Depends(
        pagination_params),
                 sorting_query_params: SortingQueryParams = Depends(sorting_params)):
        self.pagination_query_params = pagination_query_params
        self.sorting_query_params = sorting_query_params


class Query:
    pass


class QueryManager:
    def __init__(self, db: Session):
        self.db = db

    def assemble_query(self, url):
        query = Query(url)
        query.sort()
        query.filter()
        query.paginate()

        return query

    def execute_query(self, query: Query):
        return query.first()
