from fastapi import APIRouter, Depends, HTTPException, Request, Response, Form
from pydantic import BaseModel, Field
from models import Users
from typing import Annotated, Optional
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import RedirectResponse
from database import SessionLocal
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWSError, ExpiredSignatureError
from datetime import timedelta, datetime, timezone
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

templates = Jinja2Templates(directory="templates")

router = APIRouter(
    prefix= "/auth",
    tags= ['auth']
)

SECRET_KEY = "b1edc52915d828b8909c822568a7618dd4dfa0bafd0eafdea47629292a8c831d"
ALGORITHM = "HS256"

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

Oauth_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

def get_db():
    db = SessionLocal()
    try:
        yield db

    finally:
        db.close()

db_depends = Annotated[Session, Depends(get_db)]

class LoginForm:
    def __init__(self, request: Request):
        self.request: Request =request
        self.username: Optional[str]=None
        self.password: Optional[str]=None

    async def create_oauth_form(self):
        form = await self.request.form()
        self.username = form.get('email')
        self.password = form.get('password') 

def verify_password(password, hashed_password):
    if not bcrypt_context.verify(password,hashed_password):
        return False
    return True

def get_hashed_password(password):
    return bcrypt_context.hash(password)

def authenticate_user(username: str, password: str, db):
    user = db.query(Users).filter(Users.username == username).first()

    if not user:
        return False

    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user


def create_access_token(username: str, user_id: int, user_role: str, expiredelta: timedelta):
    encode = {
        'sub': username,
        'id': user_id,
        'user_role': user_role
    }
    expire = datetime.now(timezone.utc)+expiredelta
    encode.update({'exp': expire})

    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)
 
@router.get('/register',response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse('register.html', {'request': request})

@router.post("/register", response_class=HTMLResponse)
async def creatre_register(request: Request, email:str=Form(...), username:str=Form(...),
                   firstname:str=Form(...), lastname:str=Form(...), password1:str=Form(...), password2:str=Form(...), db: Session=Depends(get_db)):
    validate1 = db.query(Users).filter(Users.username==username).first()
    validate2 = db.query(Users).filter(Users.email==email).first()

    if password1!=password2 or validate1 is not None or validate2 is not None:
        msg = "Invalid Registration"
        return templates.TemplateResponse('register.html', {'request': request, 'msg': msg})

    user_model = Users()
    user_model.username = username
    user_model.email = email
    user_model.first_name = firstname
    user_model.last_name = lastname
    user_model.hashed_password = bcrypt_context.hash(password1)
    user_model.is_active = True
    user_model.phone = "7806861983"
    user_model.role=""
    db.add(user_model)
    db.commit()

    return templates.TemplateResponse("login.html", {'request': request, 'msg': 'User Successfully Created'})
 
@router.get('/logout')
async def logout(request: Request):
    msg = "Logout Successful"

    response = templates.TemplateResponse('login.html', {'request': request, 'msg': msg})
    response.delete_cookie(key='access_token')

    return response

async def get_current_user(request: Request):
    try:
        token = request.cookies.get("access_token")
        if token is None:
            return None
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username:str = payload.get('sub')
        user_id: int = payload.get('id')
        user_role: str = payload.get('user_role')

        if username is None and user_id is None:
            logout(request)        
        return {'username': username, 'id': user_id, 'user_role': user_role}
    
    except ExpiredSignatureError:
        await logout(request)
    except JWSError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not Validate user")

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/token", response_model=Token)
async def login_for_access_token(response: Response, form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_depends):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        return False
    
    token = create_access_token(user.username, user.id,user.role, timedelta(minutes=60))
    response.set_cookie(key="access_token", value=token, httponly=True)
    return True 

@router.get("/", response_class=HTMLResponse)
async def authentication_page(request: Request):
    return templates.TemplateResponse("login.html", {'request': request})

@router.post("/", response_class=HTMLResponse)
async def login(request: Request, db:Session=Depends(get_db)):
    try:
        form = LoginForm(request)
        await form.create_oauth_form()
        response = RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)
        validate_user_cookie = await login_for_access_token(response=response, form_data=form, db=db)
        
        if not validate_user_cookie:
            msg = "Invaid username or password"
            return templates.TemplateResponse('login.html', {'request': request, 'msg': msg})
        
        return response
    
    except HTTPException:
        msg = "Unknown error"
        return templates.TemplateResponse('login.html', {'request': request, 'msg': msg})
    

