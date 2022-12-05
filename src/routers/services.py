from fastapi import APIRouter, Depends, Header
from pydantic import UUID4
from sqlalchemy.orm import Session

from .. import models, oauth2
from ..config import settings
from ..database import get_db
from ..exceptions import ResourceNotFoundHTTPException
from ..schemas.service import (
    CreateService, ReturnService,
    ReturnServiceDetailed,
)
from ..utils import get_language_code_from_header, get_user_language_id

router = APIRouter(prefix=settings.BASE_URL + "/services", tags=["Services"])


@router.get("", response_model=list[ReturnService])
def get_services(
    db: Session = Depends(get_db), accept_language: str | None = Header(None)
):
    language_code = get_language_code_from_header(accept_language)

    services_db = (
        db.query(models.Service, models.ServiceTranslations)
        .join(models.ServiceTranslations)
        .join(models.Language)
        .where(models.Language.code == language_code)
        .all()
    )

    services = []
    for service, translation in services_db:
        service.name = translation.name
        service.description = translation.description
        services.append(service)

    return services


@router.get("/details", response_model=list[ReturnServiceDetailed])
def get_services_details(db: Session = Depends(get_db),
                         admin_session=Depends(oauth2.get_admin)):
    admin = admin_session.admin

    language_id = get_user_language_id(db, admin.id)

    services_db = db.query(models.Service).all()

    for service_db in services_db:
        service_translation = (
            db.query(
                models.ServiceTranslations.name, models.ServiceTranslations.description
            )
            .where(models.ServiceTranslations.language_id == language_id)
            .where(models.ServiceTranslations.service_id == service_db.service.id)
            .first()
        )
        service_db.name = service_translation[0]
        service_db.description = service_translation[1]

    return services_db


@router.get("/details/{uuid}", response_model=ReturnServiceDetailed)
def get_service_details(
        uuid: UUID4, db: Session = Depends(get_db),
        admin_session=Depends(oauth2.get_admin)
):
    service_db = db.query(models.Service).where(models.Service.id == uuid).first()

    if not service_db:
        raise ResourceNotFoundHTTPException()

    admin = admin_session.admin
    language_id = get_user_language_id(db, admin.id)

    service_translation = (
        db.query(
            models.ServiceTranslations.name, models.ServiceTranslations.description
        )
        .where(models.ServiceTranslations.language_id == language_id)
        .where(models.ServiceTranslations.service_id == service_db.id)
        .first()
    )
    service_db.name = service_translation[0]
    service_db.description = service_translation[1]

    return service_db


@router.get("/{uuid}", response_model=ReturnService)
def get_service(uuid: UUID4, db: Session = Depends(get_db),
                accept_language: str | None = Header(None)):
    language_code = get_language_code_from_header(accept_language)

    service_db = (db.query(models.Service, models.ServiceTranslations)
                  .join(models.ServiceTranslations)
                  .join(models.Language)
                  .where(models.Language.code == language_code)
                  .where(models.Service.id == uuid).first())

    if not service_db:
        raise ResourceNotFoundHTTPException()

    service = service_db[0]
    translation = service_db[1]

    service.name = translation.name
    service.description = translation.description

    return service


@router.post("")
def create_service(
        service: CreateService,
        db: Session = Depends(get_db),
        admin_session=Depends(oauth2.get_admin),  # TODO: events
):
    raise NotImplementedError  # todo: finish
    new_service = models.Service(**service.dict())

    db.add(new_service)
    db.commit()

    return new_service


@router.put("/service/{service_id}")
def update_service(
        service_id: UUID4,
        service_data: CreateService,
        db: Session = Depends(get_db),
        admin_session=Depends(oauth2.get_admin),  # TODO: events
):
    raise NotImplementedError  # todo: finish
    service_db = db.query(models.Service).where(models.Service.id == service_id).first()

    if not service_db:
        raise ResourceNotFoundHTTPException()

    service_db.name = service_data.name
    service_db.min_price = service_data.min_price
    service_db.max_price = service_data.max_price
    service_db.average_time_minutes = service_data.average_time_minutes
    service_db.description = service_data.description

    db.commit()

    return service_db


@router.post("/service/service_id")
def delete_service(
    service_id: UUID4,
    db: Session = Depends(get_db),
    admin_session=Depends(oauth2.get_admin),  # TODO: events
):
    raise NotImplementedError  # todo: finish

    service_db = db.query(models.Service).where(models.Service.id == service_id).first()

    if not service_db:
        raise ResourceNotFoundHTTPException()

    service_db.deleted = True

    db.commit()

    return service_db
