from pydantic import BaseModel


class TradeDecision(BaseModel):
    asset: str
    action: str
    confidence: float
    position_size: float
    stop_loss: float
    take_profit: float
    reasoning: str