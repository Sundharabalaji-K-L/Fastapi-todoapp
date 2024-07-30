from fastapi import APIRouter, HTTPException, Path, Depends
from typing import Annotated
from models import Todos, Users
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from starlette import status
from database import SessionLocal
from .auth import get_current_user
from passlib.context import CryptContext

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserVerification(BaseModel):
    password: str
    new_password:str = Field(min_length=6)

router = APIRouter(
    prefix="/user",
    tags=['user']
)

def get_db():
    db = SessionLocal()
    try:
        yield db

    finally:
        db.close()

db_depends = Annotated[Session, Depends(get_db)]

user_depends = Annotated[dict, Depends(get_current_user)]

@router.get("/", status_code=status.HTTP_200_OK)
async def get_user(user: user_depends, db: db_depends):
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    
    return db.query(Users).filter(Users.id==user.get('id')).first()

@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(user: user_depends, db: db_depends, user_request: UserVerification):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")
    
    user_model = db.query(Users).filter(Users.id==user.get('id')).first()

    if not bcrypt_context.verify(user_request.password, user_model.hashed_password):
         raise HTTPException(status_code=401, detail="Error on Password Change")
    
    user_model.hashed_password = bcrypt_context.hash(user_request.new_password)
    db.add(user_model)
    db.commit()
