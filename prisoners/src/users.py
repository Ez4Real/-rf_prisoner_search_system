import jwt

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from passlib.hash import bcrypt

from prisoners.src.models import User
from prisoners.src.schemas import User_Pydantic, RegisterForm, Token, UserModel
from prisoners.dependencies import JWT_SECRET, ACCESS_TOKEN_EXPIRE_MINUTES, authenticate_user, get_current_user


users_views = APIRouter()


# @users_views.post('/token', response_model=Token)
# async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
#     user = await authenticate_user(form_data.username, form_data.password)
#     if not user:
#         raise HTTPException(
#             status_code=400, 
#             detail='Неверный email или пароль'
#         )
#     access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = create_access_token(
#         data={"email": user.email, 
#               "scopes": form_data.scopes},
#         expires_delta=access_token_expires,
#     )
#     return {'access_token' : access_token,
#             'token_type' : 'bearer',
#             'scopes': form_data.scopes}

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
            'expired': 1800,
            'role': user_obj.roles}


@users_views.post('/', response_model=User_Pydantic)
async def createUser(user: RegisterForm = Depends(RegisterForm.as_form)):
    user_obj = User(email = user.email,
                    password = bcrypt.hash(user.password),
                    name=user.name,
                    phone_number=user.phone_number,
                    roles=user.roles)
    await user_obj.save()
    return await User_Pydantic.from_tortoise_orm(user_obj)


@users_views.get('/me', response_model=User_Pydantic)
async def read_users_me(current_user: User_Pydantic = Depends(get_current_user)):
    return current_user