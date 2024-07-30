import sys
sys.path.append("..")

from starlette import status
from starlette.responses import RedirectResponse
from fastapi import Request, Form, APIRouter, Depends
import models
from database import SessionLocal, engine
from sqlalchemy.orm import Session
from pydantic import BaseModel
from .auth import get_current_user, verify_password, get_hashed_password
from fastapi.responses import HTMLResponse 
from fastapi.templating import Jinja2Templates

router = APIRouter(
    prefix="/users",
    tags=['users'],
    responses={404: {'description': 'Not Found'}}
)

models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Verification(BaseModel):
    username: str
    password: str
    new_password: str


@router.get("/edit-password", response_class=HTMLResponse)
async def edit_user_view(request: Request):
    user = await get_current_user(request)
    
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    

    return templates.TemplateResponse('edit-user-password.html', {'request': request, 'user': user})


@router.post('/edit-password', response_class=HTMLResponse)
async def user_password_change(request: Request, username:str=Form(...),
                               password:str=Form(...), password2:str=Form(...), db: Session=Depends(get_db)):
    
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url='/auth', status_code=status.HTTP_302_FOUND)
    
    user_data = db.query(models.Users).filter(models.Users.username==username).first()
    msg = "Invalid username or password"

    if user_data is not None:
        if user_data.username == username and verify_password(password, user_data.hashed_password):
            user_data.hashed_password = get_hashed_password(password2)
            db.add(user_data)
            db.commit()
            msg = "Password updated"

    
    return templates.TemplateResponse('edit-user-password.html', {'request': request, 'user':user, 'msg': msg})
