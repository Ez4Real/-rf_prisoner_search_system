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
from prisoners.src.schemas import Prisoner_Pydantic, User_Pydantic, TokenData, UserModel
from prisoners.config import conf


JWT_SECRET = 'hatersgonnahate'

ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30


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
    

def age_categorise(row):
    if pd.isna(row['Age']):
        return pd.NA
    if 15 < row['Age'] < 31:
        return 'Молодой возраст'
    elif 30 < row['Age'] < 46:
        return 'Средний возраст'
    return 'Старший возраст'
    
def rank_categorise(row):
    soldiers = ['рядовой', 'ефрейтор', 'младший сержант',
                'сержант', 'сержант\t', 'старший сержант', 
                'старшина', 'старший сержант\t']
    ensigns = ['прапорщик', 'старший прапорщик', 'страший прапорщик']
    senior_officers = ['майор', 'подполковник', 'підполковник', 
                       'полковник ', 'полковник', 'капитан 2-го ранга', 
                       'капитан 1 ранга', 'капитан 3 ранга', 'капитан 2 ранга']
    higher_officers = ['генерал-майор', 'генерал армии', 'генерал-лейтенант',
                       'генерал-полковник', 'контр-адмирал']
    if pd.isna(row['Rank']):
        return pd.NA
    if row['Rank'].lower() in soldiers: return 'нижние чины'
    elif row['Rank'].lower() in ensigns: return 'прапорщики и мичманы'
    elif row['Rank'].lower() in senior_officers: return 'старшие офицеры'
    elif row['Rank'].lower() in higher_officers: return 'высшие офицеры'
    else: return 'младшие офицеры'
    
def status_categorise(row, status):
    if not isinstance(row['Status'], list):
        return pd.NA
    if status in row['Status']: 
        return True
    else: 
        return False    
    
    
async def create_dataframe():
    prisoners_data = await Prisoner_Pydantic.from_queryset(Prisoner.all())
    indexes, names, old, ranks, statuses = [], [], [], [], []
    today = date.today()
    
    for prisoner in prisoners_data:
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
    df['Категории званий'] = df.apply(lambda row: rank_categorise(row), axis=1)
    print(df)
    return df


def rankCtgr_percentage_plot(df):
    df = df.drop(columns=['Status', 'Age', 'Rank', 'Name', 'AgeCtgr'], axis=1)
    df = df.dropna()
    data = df['Категории званий'].value_counts(normalize=True) * 100
    labels = ['нижние чины', 'младшие офицеры', 'старшие офицеры', 'прапорщики/мичманы', 'высшие офицеры']
    colors = sns.color_palette('mako')[1:6]
    plt.title('Процент категорий званий')
    plt.pie(data, colors = colors, autopct='%.3f%%')
    plt.legend(labels = labels, title='Категории званий', loc="lower center", bbox_to_anchor=(0.475, -0.15), ncol= 3)
    plt.savefig('prisoners/static/images/percentageRankCategories.png', dpi=100)
        
        
def ageCtgr_death_percentage_plot(df):
    df['deathStatus'] = df.apply(lambda row: status_categorise(row, 2), axis=1)
    df = df[df.Status != False]
    df = df.drop(columns=['deathStatus', 'Age', 'Rank', 'Name', 'Категории званий'], axis=1)
    df = df.dropna()
    
    data = df['AgeCtgr'].value_counts(normalize=True) * 100
    labels = ['Средний возраст', 'Молодой возраст', 'Старший возраст']
    colors = sns.color_palette('viridis')
    
    plt.clf()
    plt.title('Смертность возрастных категорий')
    plt.pie(data, colors = colors, autopct='%.1f%%')
    plt.legend(labels = labels, title='Возрастные категории', loc="lower center", bbox_to_anchor=(0.475, -0.15), ncol= 3)
    plt.savefig('prisoners/static/images/deathsAgeCategories.png', dpi=100)
    

def rankCtgr_death_percentage_plot(df):
    df['deathStatus'] = df.apply(lambda row: status_categorise(row, 2), axis=1)
    df = df[df.deathStatus != False]
    df = df.drop(columns=['Age', 'Rank', 'Name', 'AgeCtgr', 'deathStatus'], axis=1)
    df = df.dropna()
    
    data = df['Категории званий'].value_counts(normalize=True) * 100
    labels = ['нижние чины', 'младшие офицеры', 'старшие офицеры', 'прапорщики/мичманы', 'высшие офицеры']
    colors = sns.color_palette('viridis')
    plt.clf()
    plt.title('Смертность категорий званий')
    plt.pie(data, colors = colors, autopct='%.1f%%')
    plt.legend(labels = labels, title='Категории званий', loc="lower center", bbox_to_anchor=(0.475, -0.15), ncol= 3)
    plt.savefig('prisoners/static/images/deathsRankCategories.png', dpi=100)
    
    
def rankAgeCtgr_takePart_percentage(df):
    df['takePart'] = df.apply(lambda row: status_categorise(row, 1), axis=1)
    df = df[df['takePart'] != False]
    df = df.drop(columns=['Age', 'Rank', 'Name', 'Status', 'takePart'], axis=1)
    target, feature = 'AgeCtgr', 'Категории званий'
    df = df.groupby('Категории званий').value_counts(normalize=True) 
    df = df.mul(100).rename('Процент').reset_index()
    
    tP = sns.catplot(x=feature, y='Процент', hue=target, kind='bar', data=df,
                     height=4, aspect=2.2, palette=sns.color_palette("rocket")).set(title='Процент причастности к войне категорий возрастов и званий')
    tP._legend.set_title('Возрастные категории')
    tP.ax.set_ylim(0.65)
    tP.set_xlabels('Возрастные категории')
    for p in tP.ax.patches:
        txt = str(p.get_height().round(1)) + '%'
        txt_x = p.get_x()
        txt_y = p.get_height()
        tP.ax.text(txt_x,txt_y,txt)
    tP.savefig('prisoners/static/images/rankAgeCtgrTakePart.png', dpi=100)


def rankAgeCtgr_deathStatus_count(df):
    df['deathStatus'] = df.apply(lambda row: status_categorise(row, 2), axis=1)
    df = df[df['deathStatus'] != False]
    df = df.drop(columns=['Age', 'Rank', 'Name', 'Status', 'deathStatus'], axis=1)
    df = df.dropna()
    target, feature = 'AgeCtgr', 'Категории званий'
    df = df.groupby('Категории званий').value_counts()
    df = df.rename('Количество').reset_index()
    data = df[df['Категории званий'] != 'высшие офицеры']

    dS = sns.catplot(x=feature, y='Количество', hue=target, kind='bar', data=data,
                     height=4, aspect=2, palette=sns.color_palette("rocket")[2:5]).set(title='Количество смертности на войне категорий возрастов и званий')
    dS._legend.set_title('Возрастные категории')
    dS.ax.set_ylim(0.65)
    for p in dS.ax.patches:
        txt = str(p.get_height().astype(int))
        txt_x = p.get_x()
        txt_y = p.get_height()
        dS.ax.text(txt_x,txt_y,txt)
    dS.savefig('prisoners/static/images/rankAgeCtgrDeathStatus.png', dpi=100)
    

def rankAgeCtgr_prisonerStatus_count(df):
    df['prisonerStatus'] = df.apply(lambda row: status_categorise(row, 3), axis=1)
    df = df[df['prisonerStatus'] != False]
    df = df.drop(columns=['Age', 'Rank', 'Name', 'Status', 'prisonerStatus'], axis=1)
    df = df.dropna()
    feature, target = 'AgeCtgr', 'Категории званий'
    df = df.groupby('AgeCtgr').value_counts()
    df = df.rename('Количество').reset_index()

    pS = sns.catplot(x=feature, y='Количество', hue=target, kind='bar', data=df, 
                     height=5, aspect=1.5, palette=sns.color_palette("magma")).set(title='Количество военнопленных категорий возрастов и званий')
    pS.ax.set_ylim(0.65)
    pS.set_xlabels('Возрастные категории')
    for p in pS.ax.patches:
        txt = str(p.get_height().astype(int))
        txt_x = p.get_x()
        txt_y = p.get_height()
        pS.ax.text(txt_x,txt_y,txt)
    pS.savefig('prisoners/static/images/rankAgeCtgrPrisonerStatus.png', dpi=100)
    
    
def rankAgeCtgr_investigateStatus_percentage(df):
    df['investigateStatus'] = df.apply(lambda row: status_categorise(row, 4), axis=1)
    df = df[df['investigateStatus'] != False]
    df = df.drop(columns=['Age', 'Rank', 'Name', 'Status', 'investigateStatus'], axis=1)
    df = df.dropna()
    feature, target = 'AgeCtgr', 'Категории званий'
    df = df.groupby('AgeCtgr').value_counts(normalize=True) 
    df = df.mul(100).rename('Процент').reset_index()

    print(len(sns.color_palette("crest")))

    iS = sns.catplot(x=feature, y='Процент', hue=target, kind='bar', data=df,
                     height=5, aspect=1.3, palette=sns.color_palette("viridis")).set(title='Процент расследований касательно категорий возрастов и званий')
    iS.ax.set_ylim(0.65)
    iS.set_xlabels('Возрастные категории')
    for p in iS.ax.patches:
        txt = str(p.get_height().round(1)) + '%'
        txt_x = p.get_x()
        txt_y = p.get_height()
        iS.ax.text(txt_x,txt_y,txt)
    iS.savefig('prisoners/static/images/rankAgeCtgrInvestigateStatus.png', dpi=100)
