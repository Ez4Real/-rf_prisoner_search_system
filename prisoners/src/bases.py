from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates   
from tortoise.contrib.fastapi import HTTPNotFoundError

from prisoners.src.models import MilitaryBase
from prisoners.src.schemas import MilitaryBase_Pydantic


bases_views = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

@bases_views.get('/',
                     response_class=HTMLResponse,
                     response_model=MilitaryBase_Pydantic,
                     responses={404: {"model": HTTPNotFoundError}})
async def get_current_prisoner(request: Request):
    bases_data = await MilitaryBase_Pydantic.from_queryset(MilitaryBase.all())
    return templates.TemplateResponse('military_bases.html', {"request": request, "bases_data": bases_data}) 
