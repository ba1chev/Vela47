from pydantic import BaseModel


class AddInput(BaseModel):
    a: int
    b: int
