from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ztp_api.api.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        statement = select(self.model).where(self.model.id == id)
        response = await db.execute(statement)
        target_obj = response.scalars().first()
        return target_obj

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100, **kwargs
    ) -> List[ModelType]:
        statement = select(self.model)
        filter_params = {
            column: value
            for column, value in kwargs.items()
            if value
        }
        if filter_params:
            statement = statement.filter_by(filter_params)
        statement = statement.offset(skip).limit(limit)
        response = await db.execute(statement)
        target_obj = response.scalars().all()
        return target_obj

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore
        db.add(db_obj)
        await db.commit()
        return db_obj

    async def update(self, db: AsyncSession, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: int) -> ModelType:
        statement = select(self.model).filter_by(id=id)
        response = await db.execute(statement)
        target_obj = response.scalars().first()
        await db.delete(target_obj)
        await db.commit()
        return target_obj
