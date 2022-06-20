from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates   
from tortoise.contrib.fastapi import HTTPNotFoundError

auth_views = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

@auth_views.get('/register',
                response_class=HTMLResponse,
                responses={404: {"model": HTTPNotFoundError}})
async def register_page(request: Request):
    return templates.TemplateResponse('register.html', {"request": request})


@auth_views.get('/login',
                response_class=HTMLResponse,
                responses={404: {"model": HTTPNotFoundError}})
async def login_page(request: Request):
    return templates.TemplateResponse('login.html', {"request": request})
