from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates 

from prisoners.dependencies import create_dataframe, ageCtgr_death_percentage_plot
from prisoners.src.models import Prisoner
from prisoners.src.schemas import Prisoner_Pydantic

analytics_views = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@analytics_views.get('/',
                     response_class=HTMLResponse,)
async def return_dataframe(request: Request):
    df = await create_dataframe()
    max = df['Age'].max(axis = 0, skipna = True)
    max_count = len(df[df.Age == df.Age.max()])
    mean = round(df['Age'].mean(axis = 0, skipna = True))
    min = df['Age'].min(axis = 0, skipna = True)
    min_count = len(df[df.Age == df.Age.min()])
    
    # ageCtgr_death_percentage_plot(df)

    return templates.TemplateResponse('analytics.html', {'request': request, 
                                                         'mean': mean, 
                                                         'min': min,
                                                         'min_count': min_count,
                                                         'max': max,
                                                         'max_count': max_count}) 

                     


@analytics_views.get('/{prisoner_id}')
async def get_prisoner_by_id(prisoner_id: int):
    prisoner_data = await Prisoner_Pydantic.from_queryset_single(Prisoner.get(id=prisoner_id))
    return prisoner_data
