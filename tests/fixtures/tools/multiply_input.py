from pydantic import BaseModel


class MultiplyInput(BaseModel):
    x: float
    y: float
