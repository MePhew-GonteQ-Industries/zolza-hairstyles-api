from fastapi import APIRouter, Depends, Header
from pydantic import UUID4
from sqlalchemy.orm import Session

from .. import models, oauth2
from ..config import settings
from ..database import get_db
from ..exceptions import ResourceNotFoundHTTPException
from ..schemas.service import ReturnService, ReturnServiceDetailed, \
    Service, UpdateService
from ..utils import get_language_code_from_header

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
def create_service(
        service: Service,
        db: Session = Depends(get_db),
        admin_session=Depends(oauth2.get_admin),  # TODO: events
):
    new_service = models.Service(**service.dict())

    db.add(new_service)
    db.commit()

    return new_service


@router.put("/service/{service_id}")
def update_service(
        service_id: UUID4,
        service_data: UpdateService,
        db: Session = Depends(get_db),
        admin_session=Depends(oauth2.get_admin)  # TODO: events
):
    service_db = db.query(models.Service).where(
        models.Service.id == service_id
    ).first()

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
    service_db = db.query(models.Service).where(
        models.Service.id == service_id
    ).first()

    if not service_db:
        raise ResourceNotFoundHTTPException()

    raise NotImplementedError
    service_db.deleted = True

    db.commit()

    return service_db
