import sys
sys.path.append("..")

from database import engine, SessionLocal
from typing import Optional
from pydantic import BaseModel
from starlette import status
import models
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException
from .auth import get_current_user

router = APIRouter(
    prefix='/address',
    tags= ['address'],
    responses={404: {'description': 'Not Found'}}
)

def get_db():
    db = SessionLocal()
    try:
        yield db

    finally:
        db.close()


class Address(BaseModel):
    address1: str
    address2: Optional[str]
    city: str
    state: str
    country: str
    postalcode: str

@router.post("/", status_code=status.HTTP_201_CREATED)

async def create_address(address: Address, user: dict=Depends(get_current_user),db: Session=Depends(get_db)):
    
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed')
    
    address_model = models.Address()
    address_model.address1 = address.address1
    address_model.address2 = address.address2
    address_model.city = address.city
    address_model.state = address.state
    address_model.country = address.country
    address_model.postalcode = address.postalcode

    db.add(address_model)
    db.flush()

    user_model = db.query(models.Users).filter(models.Users.id==user.get('id')).first()
    user_model.address_id = address_model.id
    db.add(user_model)
    db.commit() 