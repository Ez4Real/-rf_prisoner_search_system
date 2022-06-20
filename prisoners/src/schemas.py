from datetime import date
from typing import List

from pydantic import BaseModel
from fastapi import Form
from tortoise.contrib.pydantic import pydantic_model_creator

from prisoners.src.models import User, Prisoner, MilitaryBase, PrisonerRequest


class RegisterForm(BaseModel):
    email: str 
    password: str
    name: str
    phone_number: str
    @classmethod
    def as_form(cls,
                email: str = Form(default=None),
                password: str = Form(default=None),
                name: str = Form(default=None),
                phone_number: str = Form(default=None)
                ):
        return cls(email=email, password=password, name=name, phone_number=phone_number)


class RequestForm(BaseModel):
        family_relation: str
        @classmethod
        def as_form(cls, 
                    family_relation: str = Form(default=None)):
                return cls(family_relation=family_relation)


class MilitaryBaseModel(BaseModel):
        id: int 
        name: str | None
        soldiers: int | None = None
        longitude: str | None = None
        latitude: str | None = None
        take_part: bool


class TokenData(BaseModel):
    email: str | None = None
    scopes: List[str] = []
        
           
User_Pydantic = pydantic_model_creator(User, name='User')
Prisoner_Pydantic = pydantic_model_creator(Prisoner, name='Prisoner')
MilitaryBase_Pydantic = pydantic_model_creator(MilitaryBase, name='Base')
Request_Pydantic = pydantic_model_creator(PrisonerRequest, name='Request')
        

