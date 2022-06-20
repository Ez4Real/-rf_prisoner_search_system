from pathlib import Path

from fastapi import APIRouter, Request

from prisoners.dependencies import create_dataframe
from prisoners.src.models import Prisoner
from prisoners.src.schemas import Prisoner_Pydantic

analytics_views = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent


@analytics_views.get('/')
async def return_dataframe():
    # prisoners_data = await Prisoner_Pydantic.from_queryset(Prisoner.filter(id__lt=3))
    # for i in prisoners_data:
    #     print(i.id)
    # return prisoners_data
    return await create_dataframe()
    
    
