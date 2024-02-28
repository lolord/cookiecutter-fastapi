from typing import Generic, Optional, Type, TypeVar

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from odmantic import Model, ObjectId
from pydantic import BaseModel
from schemas.request import PaginationQuery
from schemas.response import PaginationResp

from db.mongodb import engine, find_pagination

ModelType = TypeVar("ModelType", bound=BaseModel)
ORMModelType = TypeVar("ORMModelType", bound=Model)


class CRUDBase(Generic[ModelType]):
    def __init__(self, cls: Type[ORMModelType], router=None) -> None:
        assert cls
        if router is None:
            router = APIRouter(
                prefix="/" + cls.__name__.lower(),
                tags=[cls.__name__],
            )
        self.router = router
        self.model_class = cls

        self.model_name = cls.__name__
        self.done = False

    def build(self):
        if not self.done:
            self.router.get(
                "",
                summary=f"{self.model_name}列表",
                response_model=PaginationResp[self.model_class],
            )(self.get_items_builder())
            self.router.get(
                "/{pk}",
                summary=f"{self.model_name}详细",
                response_model=self.model_class,
            )(self.get_item_builder())
            self.router.post(
                "", summary=f"{self.model_name}新增", response_model=self.model_class
            )(self.post_item_builder())
            self.router.put(
                "", summary=f"{self.model_name}修改", response_model=self.model_class
            )(self.put_item_builder())
            self.router.delete(
                "/{pk}", summary=f"{self.model_name}删除", response_model=None
            )(self.delete_item_builder())
            self.done = True
        return self.router

    def get_items_builder(self):
        async def get_items(pagination_query: PaginationQuery = Depends()):
            return await find_pagination(
                engine, self.model_class, query=pagination_query
            )

        return get_items

    def get_item_builder(self):
        async def get_item(
            id: ObjectId = Query(...),
        ) -> Optional[Model]:
            return await engine.find_one(self.model_class, {"id": id})

        return get_item

    def post_item_builder(self):
        async def post_item(item: ORMModelType = Body(...)) -> ORMModelType:
            exists = await engine.find_one(self.model_class, {"id": id})
            if exists:
                raise HTTPException(
                    status_code=400,
                    detail="Already exists",
                )
            return await engine.save(item)

        return post_item

    def put_item_builder(self):
        async def put_item(item: ORMModelType = Body(...)) -> ORMModelType:
            exists = await engine.count(self.model_class, {"id": item.id})
            if exists:
                await engine.save(item)
                return item
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Object does not exist",
                )

        return put_item

    def delete_item_builder(self):
        async def delete_item(id: ObjectId = Query(...)):
            instance = await engine.find_one(self.model_class, {"id": id})
            if instance:
                await engine.delete(instance)

        return delete_item
