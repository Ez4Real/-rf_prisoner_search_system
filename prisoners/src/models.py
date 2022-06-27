from email.policy import default
from tortoise import fields
from tortoise.models import Model
from passlib.hash import bcrypt


class MilitaryBase(Model):
    id = fields.IntField(pk=True) 
    name = fields.CharField(100, unique=True)
    soldiers = fields.IntField(null=True)
    longitude = fields.CharField(255, null=True)
    latitude = fields.CharField(255, null=True)
    take_part = fields.BooleanField(default=False)
    
    def __str__(self):
        return self.name, self.soldiers
    

class Prisoner(Model):
    id = fields.IntField(pk=True) 
    name = fields.CharField(255)
    military_base = fields.ForeignKeyField('models.MilitaryBase', null=True, related_name='prisoners') 
    date_of_birth = fields.DateField(null = True)
    rank = fields.CharField(45, null = True)
    adress = fields.CharField(510, null = True)
    
    def __str__(self):
        return self.name, self.date_of_birth, self.rank
    
    
class Info(Model):
    id = fields.IntField(pk=True) 
    name = fields.CharField(255)
    
    def __str__(self):
        return self.name
    
class Source(Model):
    id = fields.IntField(pk=True) 
    prisoner = fields.ForeignKeyField('models.Prisoner') 
    info = fields.ForeignKeyField('models.Info') 
    link = fields.CharField(2048)
    

class Status(Model):
    id = fields.IntField(pk=True) 
    name = fields.CharField(45)
    
    def __str__(self):
        return self.name
   
class StatInstance(Model):
    id = fields.IntField(pk=True)   
    prisoner = fields.ForeignKeyField('models.Prisoner') 
    status = fields.ForeignKeyField('models.Status') 
    
    
class User(Model):
    id = fields.IntField(pk=True)
    email = fields.CharField(255, unique=True) 
    password = fields.CharField(128, min_length=8)
    name = fields.CharField(255)
    phone_number = fields.CharField(45, unique=True)
    # disabled = fields.BooleanField(default=False)
    roles = fields.CharField(45, default='user')
    
    def verify_password(self, password):
        return bcrypt.verify(password, self.password)
    
    def __str__(self):
        return self.name, self.phone_number, self.email, self.password

    
class PrisonerRequest(Model):
    id = fields.IntField(pk=True) 
    user = fields.ForeignKeyField('models.User')
    prisoner = fields.ForeignKeyField('models.Prisoner')
    family_relation = fields.CharField(45)
    created_at = fields.DatetimeField(auto_now_add=True)
    
    def __str__(self):
        return self.family_relation
