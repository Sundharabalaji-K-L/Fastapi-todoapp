from fastapi import FastAPI
from routers import todos, auth, admin, users, address
from database import engine
import models
from starlette.staticfiles import StaticFiles
from starlette.responses import RedirectResponse
from starlette import status

app = FastAPI()
app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(admin.router)
app.include_router(users.router)
app.include_router(address.router)
app
models.Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND) 