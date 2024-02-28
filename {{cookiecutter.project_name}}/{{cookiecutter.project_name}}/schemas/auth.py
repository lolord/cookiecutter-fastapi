from typing import NewType

from pydantic import BaseModel
from odmantic import ObjectId


UserID = NewType("UserID", ObjectId)


class Token(BaseModel):
    access_token: str
    token_type: str
