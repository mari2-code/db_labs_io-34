from pydantic import BaseModel
from typing import Optional


# ---------- Result ----------
class ResultBase(BaseModel):
    session: int
    notes: Optional[str] = None
    score: Optional[float] = None


class ResultCreate(ResultBase):
    pass


class ResultUpdate(BaseModel):
    session: Optional[int] = None
    notes: Optional[str] = None
    score: Optional[float] = None


class ResultInDB(ResultBase):
    id: int

    class Config:
        from_attributes = True


# ---------- SessionResultLink ----------
class SessionResultLinkBase(BaseModel):
    session_id: int
    session_account_id: int
    result_id: int


class SessionResultLinkCreate(SessionResultLinkBase):
    pass


class SessionResultLinkInDB(SessionResultLinkBase):
    class Config:
        from_attributes = True
