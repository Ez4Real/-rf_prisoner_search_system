import jwt

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from passlib.hash import bcrypt

from prisoners.src.models import User
from prisoners.src.schemas import User_Pydantic
from prisoners.src.schemas import RegisterForm
from prisoners.dependencies import JWT_SECRET, authenticate_user, get_current_user


users_views = APIRouter()


@users_views.post('/token')
async def generate_token(form_data: OAuth2PasswordRequestForm = Depends()):
    try: 
        user = await authenticate_user(form_data.username, form_data.password)
    except: 
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail='Неверный email или пароль'
        )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail='Неверный email или пароль'
        )
    user_obj = await User_Pydantic.from_tortoise_orm(user)

    token = jwt.encode(user_obj.dict(), JWT_SECRET)

    return {'access_token' : token,
            'token_type' : 'bearer',
            'expired': 1800}


@users_views.post('/', response_model=User_Pydantic)
async def createUser(user: RegisterForm = Depends(RegisterForm.as_form)):
    user_obj = User(email = user.email, 
                    password = bcrypt.hash(user.password),
                    name=user.name,
                    phone_number=user.phone_number)
    await user_obj.save()
    return await User_Pydantic.from_tortoise_orm(user_obj)


@users_views.get('/me', response_model=User_Pydantic)
async def get_user(user: User_Pydantic = Depends(get_current_user)):
    return user