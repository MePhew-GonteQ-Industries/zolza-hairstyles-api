from typing import List

import langcodes
from fastapi import APIRouter, Depends, Header
from pydantic import UUID4
from sqlalchemy.orm import Session

from .. import models, oauth2
from ..config import settings
from ..database import get_db
from ..exceptions import ResourceNotFoundHTTPException
from ..schemas.service import CreateServices, ReturnService, ReturnServiceDetailed
from ..schemas.user_settings import DefaultContentLanguages

router = APIRouter(prefix=settings.BASE_URL + "/services", tags=["Services"])


@router.get("", response_model=list[ReturnService])
def get_services(
    db: Session = Depends(get_db), accept_language: str | None = Header(None)
):
    accept_language = accept_language.split(',')[0].split(';')[0]
    if accept_language:
        language = langcodes.Language.get(langcodes.standardize_tag(accept_language))

        if language.is_valid():
            language_code = language.language
        else:
            language_code = DefaultContentLanguages.polish.value
    else:
        language_code = DefaultContentLanguages.polish.value

    services_db = (
        db.query(models.Service, models.ServiceTranslations)
        .join(models.ServiceTranslations)
        .join(models.Language)
        .where(models.Language.code == language_code)
        .all()
    )

    services = []
    for service in services_db:
        service[0].name = service[1].name
        service[0].description = service[1].description
        services.append(service[0])

    return services


@router.get("/details", response_model=list[ReturnServiceDetailed])
def get_services_details(db: Session = Depends(get_db), _=Depends(oauth2.get_admin)):
    services_details = db.query(models.Service).all()

    return services_details


@router.get("/details/{uuid}", response_model=ReturnServiceDetailed)
def get_service_details(
    uuid: UUID4, db: Session = Depends(get_db), _=Depends(oauth2.get_admin)
):
    service_details = db.query(models.Service).where(models.Service.id == uuid).first()

    if not service_details:
        raise ResourceNotFoundHTTPException()

    return service_details


@router.get("/{uuid}", response_model=ReturnService)
def get_service(uuid: UUID4, db: Session = Depends(get_db)):
    service = db.query(models.Service).where(models.Service.id == uuid).first()

    if not service:
        raise ResourceNotFoundHTTPException()

    return service


@router.post("")
def create_services(
    services: CreateServices,
    db: Session = Depends(get_db),
    admin_session=Depends(oauth2.get_admin),
):
    raise NotImplementedError

    # return services


@router.put("")
def update_services(db: Session = Depends(get_db), _=Depends(oauth2.get_admin)):
    raise NotImplementedError()


@router.put("/service/{uuid}")
def update_service(
    uuid: UUID4, db: Session = Depends(get_db), _=Depends(oauth2.get_admin)
):
    raise NotImplementedError()


@router.delete("")
def delete_services(
    services: List[UUID4],
    db: Session = Depends(get_db),
    admin_session=Depends(oauth2.get_admin),
):
    raise NotImplementedError
    # print(services)
    # return services
