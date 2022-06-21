from pathlib import Path

from fastapi import APIRouter, Request

from prisoners.dependencies import create_dataframe
from prisoners.src.models import Prisoner
from prisoners.src.schemas import Prisoner_Pydantic

analytics_views = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent


@analytics_views.get('/')
async def return_dataframe():
    df = await create_dataframe()
    mean = round(df['Old'].mean(axis = 0, skipna = True))
    min = df['Old'].min(axis = 0, skipna = True)
    return {'mean': mean, 
            'min': min}

@analytics_views.get('/{prisoner_id}')
async def get_prisoner_by_id(request: Request, prisoner_id: int):
    prisoner_data = await Prisoner_Pydantic.from_queryset_single(Prisoner.get(id=prisoner_id))
    return prisoner_data
