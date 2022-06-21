import jwt
import pandas as pd
from datetime import date
from dateutil import relativedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi_mail import MessageSchema, FastMail

from prisoners.src.models import User, Prisoner
from prisoners.src.schemas import User_Pydantic, Prisoner_Pydantic
from prisoners.config import conf


JWT_SECRET = 'hatersgonnahate'

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='users/token')


async def authenticate_user(email: str, password: str):
    user = await User.get(email=email)
    if not user:
        return False 
    if not user.verify_password(password):
        return False
    return user 


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        user = await User.get(id=payload.get('id'))
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail='Неверный email или пароль')
    return await User_Pydantic.from_tortoise_orm(user)


def get_current_user_id(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        user_id = payload.get('id')
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail='Авторизуйтесь для отправки запроса')
    return user_id


async def send_email_async(subject: str, 
                           email_to: str, 
                           body: dict,
                           template_name):
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        template_body=body,
        subtype='html',
    )
    fm = FastMail(conf)
    await fm.send_message(message, template_name=template_name)
    
    
async def create_dataframe():
    # prisoners_data = await Prisoner_Pydantic.from_queryset(Prisoner.filter(id__lt=4))
    prisoners_data = await Prisoner_Pydantic.from_queryset(Prisoner.all())
    indexes, names, old, ranks, statuses = [], [], [], [], []
    today = date.today()

    for prisoner in prisoners_data:
        indexes.append(prisoner.id)
        names.append(prisoner.name)
        if prisoner.date_of_birth:
            diff = relativedelta.relativedelta(today, prisoner.date_of_birth)
            old.append(diff.years)
        else: old.append(pd.NA)
        if prisoner.rank == '':
            ranks.append(pd.NA)
        else: ranks.append(prisoner.rank)
        prisoner_statuses = []
        if prisoner.statinstances:
            for status in prisoner.statinstances:
                prisoner_statuses.append(status.status.id)
            statuses.append(prisoner_statuses)
        else: statuses.append(pd.NA)
    list_of_tuples = list(zip(names, old, ranks, statuses))
    df = pd.DataFrame(list_of_tuples, 
                      columns=['Name', 'Old', 'Rank', 'Status'],
                      index=indexes)
    return df
        
        
