from pydantic import BaseModel


class MarketEvent(BaseModel):
    event_type: str
    description: str
    sentiment: str
    impact: str
    affected_assets: list[str]