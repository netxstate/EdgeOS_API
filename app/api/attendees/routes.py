import secrets

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.api.attendees import schemas
from app.api.attendees.crud import attendee as attendee_crud
from app.api.attendees.crud import ticket_api_key_crud
from app.core.config import settings
from app.core.database import get_db
from app.core.logger import logger

router = APIRouter()


# Search for attendees by email
@router.get('/search/email', response_model=list[schemas.Attendee])
def search_attendees_by_email(
    email: str,
    x_api_key: str = Header(...),
    db: Session = Depends(get_db),
):
    if x_api_key != settings.ATTENDEES_API_KEY:
        raise HTTPException(status_code=403, detail='Invalid API key')
    logger.info('Searching for attendees by email: %s', email)
    attendees = attendee_crud.get_by_email(db=db, email=email)
    if not attendees:
        raise HTTPException(
            status_code=404, detail='No attendees found with this email'
        )
    return attendees


@router.get('/tickets', response_model=list[schemas.AttendeeWithTickets])
def get_tickets(
    email: str,
    x_api_key: str = Header(...),
    db: Session = Depends(get_db),
):
    """Return tickets for the attendee email.

    Authentication rules:
    1. A static key defined in settings (for backward compatibility).
    2. A dynamic key stored in `attendee_ticket_api_keys` table **matching the same email**.
    """

    # 1) Static keys from settings (legacy support)
    valid_keys = [
        k
        for k in [
            settings.ATTENDEES_TICKETS_API_KEY,
            settings.ATTENDEES_TICKETS_API_KEY_2,
        ]
        if k
    ]

    if x_api_key not in valid_keys:
        # 2) Check dynamic keys
        db_key = ticket_api_key_crud.get_by_key(db, x_api_key)
        if not db_key or db_key.email.lower() != email.lower():
            raise HTTPException(status_code=403, detail='Invalid API key')

    attendees = attendee_crud.get_by_email(db=db, email=email)

    response = []
    for attendee in attendees:
        application = attendee.application
        products = [
            schemas.MinProductsData(
                name=p.name,
                category=p.category,
                start_date=p.start_date,
                end_date=p.end_date,
            )
            for p in attendee.products
        ]
        if not products and application.popup_city.applications_imported:
            products = [
                schemas.MinProductsData(
                    name=f'Ticket for {application.popup_city.name}',
                    category='ticket',
                    start_date=application.popup_city.start_date,
                    end_date=application.popup_city.end_date,
                )
            ]
        response.append(
            schemas.AttendeeWithTickets(
                name=attendee.name,
                email=attendee.email,
                category=attendee.category,
                popup_city=application.popup_city.name,
                products=products,
            )
        )
    return response


# ---------------------------------------------------------------------------
# API Key generation for /attendees/tickets
# ---------------------------------------------------------------------------


@router.post('/tickets/api-keys', response_model=schemas.TicketApiKeyResponse)
def generate_ticket_api_key(
    payload: schemas.TicketApiKeyCreate,
    x_api_key: str = Header(...),
    db: Session = Depends(get_db),
):
    """Generate a one-off API key linked to an email.

    The caller must provide a valid admin ATTENDEES_MANAGEMENT_API_KEY via the `X-API-Key` header.
    The generated key will later be used to authenticate calls to `/attendees/tickets`.
    """

    if x_api_key != settings.ATTENDEES_MANAGEMENT_API_KEY:
        raise HTTPException(status_code=403, detail='Invalid API key')

    # Generate a secure random token
    api_key = secrets.token_urlsafe(32)

    # Persist the key
    ticket_api_key_crud.create(
        db=db,
        obj=schemas.TicketApiKeyCreate(email=payload.email, key=api_key),
    )

    return schemas.TicketApiKeyResponse(email=payload.email, api_key=api_key)
