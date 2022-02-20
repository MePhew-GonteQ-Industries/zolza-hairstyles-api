from typing import List

from fastapi import APIRouter, Depends
from pydantic import UUID4
from sqlalchemy.orm import Session

from .. import models, oauth2
from ..config import settings
from ..database import get_db
from ..exceptions import ResourceNotFoundException
from ..schemas.service import CreateServices, ReturnService, ReturnServiceDetailed

router = APIRouter(prefix=settings.BASE_URL + "/services", tags=["Services"])


@router.get("", response_model=List[ReturnService])
def get_services(db: Session = Depends(get_db)):
    services = db.query(models.Service).all()

    return services


@router.get("/details", response_model=List[ReturnServiceDetailed])
def get_services_details(db: Session = Depends(get_db), _=Depends(oauth2.get_admin)):
    services_details = db.query(models.Service).all()

    return services_details


@router.get('/details/{uuid}', response_model=ReturnServiceDetailed)
def get_service_details(uuid: UUID4,
                        db: Session = Depends(get_db),
                        _=Depends(oauth2.get_admin)):
    service_details = db.query(models.Service).where(models.Service.id == uuid).first()

    if not service_details:
        raise ResourceNotFoundException()

    return service_details


@router.get("/{uuid}", response_model=ReturnService)
def get_service(uuid: UUID4, db: Session = Depends(get_db)):
    service = db.query(models.Service).where(models.Service.id == uuid).first()

    if not service:
        raise ResourceNotFoundException()

    return service


@router.post("")
def create_services(
    services: CreateServices,
    db: Session = Depends(get_db),
    admin=Depends(oauth2.get_admin),
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
    admin=Depends(oauth2.get_admin),
):
    raise NotImplementedError
    # print(services)
    # return services
