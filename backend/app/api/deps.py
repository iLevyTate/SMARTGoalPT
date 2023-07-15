import logging
from typing import Annotated

import jwt
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import PyJWTError
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import ValidationError
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND

from app.core.config import Settings, config
from app.core.security import ALGORITHM
from app.db import db_client
from app.models.token import TokenPayload
from app.models.user import UserNoGoals
from app.services.user_service import get_user_no_goal

logging.basicConfig(format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s")
logging.root.setLevel(level=config.log_level)
logger = logging

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{config.V1_API_PREFIX}/login/access-token")


def get_config() -> Settings:
    return config


def get_db_client() -> AsyncIOMotorClient:
    return db_client


async def get_current_admin_user(token: Annotated[str, Depends(_oauth2_scheme)]) -> UserNoGoals:
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)
    except (PyJWTError, ValidationError) as e:
        logger.info("Could not validate credentials: %s", e)
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials")

    try:
        oid = ObjectId(token_data.sub)
    except InvalidId:  # pragma: no cover
        logger.info("%s is not a valid ObjectId", token_data.sub)
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail=f"{token_data.sub} is not a valid ID format"
        )

    user = await get_user_no_goal(oid)

    if not user:
        logger.info("User not found")
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="User not found")

    if not user.is_admin:
        logger.info("User is not an admin")
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="User does not have the required permissions"
        )

    return user


async def get_current_user(token: Annotated[str, Depends(_oauth2_scheme)]) -> UserNoGoals:
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)
    except (PyJWTError, ValidationError) as e:
        logger.info("Could not validate credentials: %s", e)
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials")

    try:
        oid = ObjectId(token_data.sub)
    except InvalidId:  # pragma: no cover
        logger.info("%s is not a valid ObjectId", token_data.sub)
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail=f"{token_data.sub} is not a valid ID format"
        )

    user = await get_user_no_goal(oid)

    if not user:
        logger.info("User not found")
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="User not found")

    return user


Config = Annotated[Settings, Depends(get_config)]
CurrentUser = Annotated[UserNoGoals, Depends(get_current_user)]
CurrentAdminUser = Annotated[UserNoGoals, Depends(get_current_admin_user)]
MongoClient = Annotated[AsyncIOMotorClient, Depends(get_db_client)]
