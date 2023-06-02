from peewee import *
import datetime
from flask_login import UserMixin

db = PostgresqlDatabase(
    'flaskm_db',
    host='localhost',
    port=5432,
    user='flaskm_user',
    password='qwe123'
)
db.connect()

class BaseModel(Model):
    class Meta:
        database = db

class MyUser(BaseModel, UserMixin):
    email = CharField(max_length=225, null=False, unique=True)
    name = CharField(max_length=225, null=False)
    second_name = CharField(max_length=225, null=False)
    password = CharField(max_length=225, null=False)
    age = IntegerField()

    def __repr__(self):
        return self.email

class Post(BaseModel):
    title = CharField()
    description = TextField()
    image_path = CharField()
    author = ForeignKeyField(MyUser, backref='posts')
    date = DateTimeField(default=datetime.datetime.now)

    def __repr__(self):
        return self.title

class Comment(BaseModel):
    post = ForeignKeyField(Post, backref='comments')
    author = ForeignKeyField(MyUser, backref='comments')
    content = TextField()
    date = DateTimeField(default=datetime.datetime.now)

    def __repr__(self):
        return f'Comment by {self.author.email} on post {self.post.id}'

class Chats(BaseModel):
    chat = CharField()
# Создаем таблицы в базе данных
db.create_tables([MyUser, Post, Comment,Chats])
