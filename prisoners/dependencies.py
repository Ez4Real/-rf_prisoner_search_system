import jwt
import pandas as pd
import seaborn as sns
from datetime import date, datetime, timedelta
from dateutil import relativedelta

from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from fastapi_mail import MessageSchema, FastMail

from prisoners.src.models import User, Prisoner
from prisoners.src.schemas import Prisoner_Pydantic, TokenData, UserModel
from prisoners.config import conf
from pydantic import ValidationError


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
        expire = datetime.utcnow() + timedelta(minutes=15)
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
        token_data = TokenData(scopes=token_scopes, email=email)
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
    # prisoners_data = await Prisoner_Pydantic.from_queryset(Prisoner.filter(id__lt=1001))
    prisoners_data = await Prisoner_Pydantic.from_queryset(Prisoner.all())
    indexes, names, old, ranks, statuses = [], [], [], [], []
    today = date.today()
    
    for prisoner in prisoners_data:
        indexes.append(prisoner.id)
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
                      columns=['Name', 'Age', 'Rank', 'Status'],
                      index=indexes)
    df['AgeCtgr'] = df.apply(lambda row: age_categorise(row), axis=1)
    # print(df)
    return df
        
      
def age_categorise(row):
    if pd.isna(row['Age']):
        return pd.NA
    if 15 < row['Age'] < 31:
        return 'Young age'
    elif 30 < row['Age'] < 46:
        return 'Middle age'
    return 'Elderly age'

def dead_status_categorise(row):
    if not isinstance(row['Status'], list):
        return pd.NA
    if 2 in row['Status']: 
        return 'Dead'
    else: 
        return 'Not Dead'
    
def death_percentage_plot(df):
    df = df[['Status', 'AgeCtgr']]
    df['Status'] = df.apply(lambda row: dead_status_categorise(row), axis=1)
    feature, target = 'AgeCtgr', 'Status'
    df = df.dropna()
    df = df.groupby(feature)[target].value_counts(normalize=True) 
    df = df.mul(100).rename('Percent').reset_index()
    
    print(df)
    
    sns.set_theme(style="ticks")
    g = sns.catplot(x=feature, y='Percent', hue=target, kind='bar', data=df)
    g.ax.set_ylim (0,100)
    
    for p in g.ax.patches:
        txt = str(p.get_height().round(3)) + '%'
        txt_x = p.get_x()
        txt_y = p.get_height()
        g.ax.text(txt_x,txt_y,txt)
    
    g.savefig('percentage.png')
    
    
    # df_percent = pd.crosstab(df['AgeCtgr'], df['Age'],
    #                          normalize = 'index').rename_axis(None)
    # df_percent *= 100
    
    # plt.bar(df_percent.index, df_percent.Y, align='center', alpha=0.5)
    # plt.ylabel('Death rate percentage')
    # plt.title('Age Categories Death Rate Percentage')

    # plt.show()
    
    return df