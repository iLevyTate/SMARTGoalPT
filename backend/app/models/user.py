from datetime import datetime
from enum import Enum

from beanie import Document
from bson import ObjectId
from pydantic import BaseModel, Field, validator
from pymongo import ASCENDING, IndexModel

from app.models.object_id import ObjectIdStr


class RepeatsEvery(str, Enum):
    day = "day"
    week = "week"
    month = "month"


class DaysOfWeek(BaseModel):
    monday: bool = False
    tuesday: bool = False
    wednesday: bool = False
    thursday: bool = False
    friday: bool = False
    saturday: bool = False
    sunday: bool = False


class _GoalBase(BaseModel):
    name: str
    duration: int | None
    days_of_week: DaysOfWeek | None
    repeats_every: RepeatsEvery | None
    progress: float | None


class Goal(_GoalBase):
    id: str

    class Settings:
        projection = {
            "id": "$_id",
            "name": "$name",
            "days_of_week": "$days_of_week",
            "repeats_every": "$repeats_every",
            "progress": "$progress",
        }


class GoalCreate(_GoalBase):
    pass


class GoalWithUserId(Goal):
    user_id: ObjectIdStr

    class Config:
        json_encoders = {ObjectId: lambda x: str(x)}


class UserCreate(BaseModel):
    user_name: str
    password: str


class UserNoPassword(BaseModel):
    id: ObjectIdStr
    user_name: str

    class Config:
        json_encoders = {ObjectId: lambda x: str(x)}

    class Settings:
        projection = {
            "id": "$_id",
            "user_name": "$user_name",
        }


class UserWithGoals(UserNoPassword):
    goals: list[Goal] | None = None

    class Settings:
        projection = {
            "id": "$_id",
            "user_name": "$user_name",
            "goals": "$goals",
        }


class UserNoGoals(UserNoPassword):
    is_active: bool
    is_admin: bool
    date_created: datetime
    last_update: datetime
    last_login: datetime

    class Settings:
        projection = {
            "id": "$_id",
            "user_name": "$user_name",
            "is_active": "$is_active",
            "is_admin": "$is_admin",
            "date_created": "$date_created",
            "last_update": "$last_update",
            "last_login": "$last_login",
        }


class UserUpdateMe(BaseModel):
    id: ObjectIdStr
    password: str
    user_name: str

    class Config:
        json_encoders = {ObjectId: lambda x: str(x)}


class UserUpdate(UserUpdateMe):
    is_active: bool
    is_admin: bool


class User(Document):
    user_name: str
    hashed_password: str
    goals: list[Goal] | None = None
    is_active: bool = True
    is_admin: bool = False
    date_created: datetime = Field(default_factory=datetime.now)
    last_update: datetime = Field(default_factory=datetime.now)
    last_login: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "users"
        indexes = [
            IndexModel(keys=[("user_name", ASCENDING)], name="user_name", unique=True),
            IndexModel(keys=[("is_active", ASCENDING)], name="is_active"),
            IndexModel(keys=[("is_admin", ASCENDING)], name="is_admin"),
            IndexModel(keys=[("goals", ASCENDING)], name="goals"),
            IndexModel(
                keys=[("_id", ASCENDING), ("goals.id", ASCENDING)], name="goal_id", unique=True
            ),
            IndexModel(
                keys=[("_id", ASCENDING), ("goals.name", ASCENDING)], name="goal_name", unique=True
            ),
        ]

    @validator("goals")
    @classmethod
    def validate_goals(cls, v: list[Goal] | None) -> list[Goal] | None:
        """Validate that the goal names and ids are unique.

        I want this to happen in the database, but so far I haven't been able to get Beanie to do it.
        """
        if not v:
            return None

        goal_ids = {x.id for x in v}
        if len(v) != len(goal_ids):
            raise ValueError(
                "Goal IDs must be unique",
            )

        goal_names = {x.name for x in v}
        if len(v) != len(goal_names):
            raise ValueError(
                "Goal names must be unique",
            )

        return v
