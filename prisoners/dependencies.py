import jwt

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from datetime import date, datetime, timedelta
from dateutil import relativedelta

from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from fastapi_mail import MessageSchema, FastMail
from pydantic import ValidationError

from prisoners.src.models import User, Prisoner
from prisoners.src.schemas import Prisoner_Pydantic, TokenData, UserModel
from prisoners.config import conf, administrators


JWT_SECRET = 'hatersgonnahate'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl='users/token',
    scopes={"user": "Права которыми обладает пользователь",
            "admin": "Права которыми обладает администратор"})


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt


async def authenticate_user(email: str, password: str):
    user = await User.get(email=email)
    if not user:
        return False 
    if not user.verify_password(password):
        return False
    return user 


async def get_current_user(security_scopes: SecurityScopes, 
                           token: str = Depends(oauth2_scheme)):
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = f"Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": authenticate_value})
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        email: str = payload.get('email')
        if email is None:
            raise credentials_exception
        token_scopes = payload.get('scopes', [])
        
        if 'user' not in token_scopes:
            token_scopes.append('user')
        if email in administrators and 'admin' not in token_scopes:
            token_scopes.append('admin')
            
        token_data = TokenData(scopes=token_scopes, email=email)
        print(token_data)
    except (jwt.PyJWKError, ValidationError):
        raise credentials_exception
    user = User.get(email=token_data.email)
    if user is None:
        raise credentials_exception
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Недостаточно прав",
                headers={"WWW-Authenticate": authenticate_value},
            )
    return await user


async def get_current_active_user(
    current_user: UserModel = Security(get_current_user, scopes=["user"])
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Неактивный пользователь")
    return current_user


async def get_current_active_admin(
    current_user: UserModel = Security(get_current_user, scopes=["user", "admin"])
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Неактивный администратор")
    return current_user


async def send_email_async(subject: str, 
                     template_name,
                     data):
    message = MessageSchema(subject=subject,
                            recipients=[data.user.email],
                            template_body={'username': data.user.name,
                                           'userphone': data.user.phone_number,
                                           'prisoner': data.prisoner.name},
                            subtype='html',)
    fm = FastMail(conf)
    await fm.send_message(message, template_name=template_name)
    
    
async def create_dataframe():
    # prisoners_data = await Prisoner_Pydantic.from_queryset(Prisoner.filter(id__lt=5001))
    prisoners_data = await Prisoner_Pydantic.from_queryset(Prisoner.all())
    indexes, names, old, ranks, statuses = [], [], [], [], []
    today = date.today()
    
    for prisoner in prisoners_data:
        # indexes.append(prisoner.id)
        names.append(prisoner.name)
        
        if prisoner.date_of_birth:
            diff = relativedelta.relativedelta(today, prisoner.date_of_birth)
            if 15 < diff.years < 100:
                old.append(diff.years)
            else: old.append(pd.NA)
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
                      columns=['Name', 'Age', 'Rank', 'Status'])
    df['AgeCtgr'] = df.apply(lambda row: age_categorise(row), axis=1)
    print(df.Rank.unique())
    return df
        
def age_categorise(row):
    if pd.isna(row['Age']):
        return pd.NA
    if 15 < row['Age'] < 31:
        return 'Young age'
    elif 30 < row['Age'] < 46:
        return 'Middle age'
    return 'Elderly age'
    
def rank_categorise(row):
    soldiers = ['рядовой', 'ефрейтор', 'младший сержант',
                'сержант', 'сержант\t', 'старший сержант', 
                'старшина', 'старший сержант\t']
    ensigns = ['прапорщик', 'старший прапорщик', 'страший прапорщик']
    junior_officers = ['младший лейтенант', 'сатрший лейтенант', 'капитан'
                       'лейтенант медицинской службы', 'лейтенант\t',
                       'лейтенант', 'капитан-лейтенант', 'старший лейтенант гвардии',
                       'страший лейтенант', 'старший лейтенант медицинской службы',
                       'старший лейтенант\t', 'капитан гвардии', 'капитан полиции',
                       'капитан внутренних войск мвд', 'капитан медицинской службы']
    senior_officers = ['майор', 'подполковник', 'підполковник', 
                       'полковник ', 'полковник', 'капитан 2-го ранга', 
                       'капитан 1 ранга', 'капитан 3 ранга', 'капитан 2 ранга']
    higher_officers = ['генерал-майор', 'генерал армии', 'генерал-лейтенант',
                       'генерал-полковник', 'контр-адмирал']
    rank_categories = {
        soldiers: 'солдаты и матросы',
        ensigns: 'прапорщики и мичманы',
        junior_officers: 'младшие офицеры',
        senior_officers: 'старшие офицеры',
        higher_officers: 'высшие офицеры'
    }
    if pd.isna(row['Rank']):
        return pd.NA
    if rank_categories[row['Rank']].lower() in soldiers: return rank_categories[soldiers]
    elif rank_categories[row['Rank']].lower() in ensigns: return rank_categories[ensigns]
    elif rank_categories[row['Rank']].lower() in junior_officers: return rank_categories[junior_officers]
    elif rank_categories[row['Rank']].lower() in senior_officers: return rank_categories[senior_officers]
    else: return rank_categories[higher_officers]
    
def ageCtgr_death_percentage_plot(df):
    df['Status'] = df.apply(lambda row: dead_status_categorise(row), axis=1)
    df = df[df.Status != 'Not Dead']
    df = df.drop(['Status', 'Age', 'Rank', 'Name'], 1)
    df = df.dropna()
    data = df['AgeCtgr'].value_counts(normalize=True) * 100
    labels = ['Средний возраст', 'Молодой возраст', 'Старший возраст']
    colors = sns.color_palette('viridis')
    plt.title('Смертность возрастных категорий')
    plt.pie(data, labels = labels, colors = colors, autopct='%.0f%%')
    plt.savefig('deathsAgeCategories.png')
    
def dead_status_categorise(row):
    if not isinstance(row['Status'], list):
        return pd.NA
    if 2 in row['Status']: 
        return 'Dead'
    else: 
        return 'Not Dead'