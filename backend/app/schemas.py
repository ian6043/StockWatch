from pydantic import BaseModel, Field
from typing import Literal


class CreateUserRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=50)


class AddStockRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10)


class CreateRuleRequest(BaseModel):
    rule_type: Literal["price", "percent_change"]
    condition: Literal["above", "below"]
    target_value: float
    cooldown_seconds: int = Field(default=300, ge=0)


class UserResponse(BaseModel):
    id: int
    user_id: str

    class Config:
        from_attributes = True


class RuleResponse(BaseModel):
    id: int
    rule_type: str
    condition: str
    target_value: float
    cooldown_seconds: int
    last_triggered_at: float | None = None

    class Config:
        from_attributes = True


class WatchlistItemResponse(BaseModel):
    id: int
    symbol: str
    rules: list[RuleResponse] = []

    class Config:
        from_attributes = True
