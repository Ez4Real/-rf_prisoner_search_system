from datetime import datetime

from pathlib import Path

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from tortoise.contrib.fastapi import HTTPNotFoundError

from prisoners.src.models import Prisoner, PrisonerRequest
from prisoners.src.schemas import Prisoner_Pydantic, Request_Pydantic, User_Pydantic
from prisoners.dependencies import get_current_user
from prisoners.src.schemas import RequestForm


prisoners_views = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@prisoners_views.get('/',
                     response_class=HTMLResponse,
                     responses={404: {"model": HTTPNotFoundError}})
async def get_page_of_prisoners(
                                request: Request,
                                page_num: int=1,
                                page_limit: int=50):
    start = (page_num - 1) * page_limit
    end = start + page_limit

    prisoners_data = await Prisoner_Pydantic.from_queryset(Prisoner.filter(id__in=range(start, end+1)))
    prisoners_count = await Prisoner.all().count()
    
    response = {
        'request': request, 
        'prisoners_count': prisoners_count,
        'next': None,
        'previous': None,
        'prisoners_data': prisoners_data
    }
    
    if end >= prisoners_count: 
        if page_num > 1:
            response['previous'] = f"/prisoners?page_num={page_num-1}&page_limit={page_limit}"
    else:
        if page_num > 1:
            response['previous'] = f"/prisoners?page_num={page_num-1}&page_limit={page_limit}"

        response['next'] = f"/prisoners?page_num={page_num+1}&page_limit={page_limit}"
    
    return templates.TemplateResponse('prisoners.html', response)


@prisoners_views.get('/search',
                     response_class=HTMLResponse,
                     responses={404: {"model": HTTPNotFoundError}})
async def search_prisoners(request: Request, 
                           name: str | None = None,
                           base: str | None = None,
                           rank: str | None = None,
                           status: str | None = None):
    prisoners_data = await Prisoner_Pydantic.from_queryset(Prisoner.filter(name__contains=name,
                                                                           military_base__name__contains=base,
                                                                           rank__contains=rank,
                                                                           statinstances__status__id__contains=status))
    prisoners_count = await Prisoner.all().count()
    return templates.TemplateResponse('prisoners.html', {'request': request, 
                                                         "prisoners_data": prisoners_data,
                                                         "prisoners_count": prisoners_count})


@prisoners_views.get('/{prisoner_id}', 
                     response_class=HTMLResponse,
                     response_model=Prisoner_Pydantic,
                     responses={404: {"model": HTTPNotFoundError}})
async def get_prisoner_by_id(request: Request, prisoner_id: int):
    prisoner_data = await Prisoner_Pydantic.from_queryset_single(Prisoner.get(id=prisoner_id))
    
    return templates.TemplateResponse('prisoner.html', {"request": request,
                                                        "prisoner_data": prisoner_data})


@prisoners_views.post('/request/{prisonerId}', 
                      responses={404: {"model": HTTPNotFoundError}})
async def create_request(prisonerId: int,
                         request: RequestForm = Depends(RequestForm.as_form),
                         user: User_Pydantic = Depends(get_current_user)):
    request_obj = PrisonerRequest(family_relation = request.family_relation,
                                  created_at = datetime.now(),
                                  user_id = user.id,
                                  prisoner_id = prisonerId)
    await request_obj.save()
    return await Request_Pydantic.from_tortoise_orm(request_obj)
