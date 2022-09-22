from fastapi import APIRouter, Query, Depends
from ztp_api.api import crud, schemas, models
from ztp_api.api.dependencies import get_db

models_router = APIRouter(prefix='/models')


@models_router.get('/', response_model=list[schemas.Model])
async def models_list(skip: int = 0, limit: int = 100, db=Depends(get_db)):
    models = await crud.model.get_multi(db, skip=skip, limit=limit)
    return models


@models_router.post('/', response_model=schemas.Model)
async def models_create(req: schemas.ModelCreateRequest, db=Depends(get_db)):
    answer = await crud.model.create(db, obj_in=req)
    return answer


@models_router.get('/{model_id}/', response_model=schemas.Model)
async def models_read(model_id: int, db=Depends(get_db)):
    entry = await crud.model.get(db=db, id=model_id)
    return entry


@models_router.patch('/{model_id}', response_model=schemas.Model)
async def models_partial_update(req: schemas.ModelPatchRequest):
    pass


@models_router.delete('/{model_id}/')
async def models_delete(model_id: int, db=Depends(get_db)):
    answer = await crud.model.remove(db, id=model_id)
    return answer
