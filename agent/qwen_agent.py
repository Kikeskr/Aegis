import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from agent.events import MarketEvent
from agent.schemas import TradeDecision


load_dotenv()


client = OpenAI(
    api_key=os.getenv("BITGET_QWEN_API_KEY"),
    base_url="https://hackathon.bitgetops.com/v1",
)


def analyze_event(
    event: MarketEvent,
    current_positions: dict | None = None,
) -> TradeDecision:

    if current_positions is None:
        current_positions = {}

    portfolio_context = []

    for asset, position in current_positions.items():

        side = position.get("side", "LONG")
        quantity = position.get("quantity", 0.0)
        entry_price = position.get("entry_price", 0.0)

        portfolio_context.append(
            {
                "asset": asset,
                "side": side,
                "quantity": quantity,
                "entry_price": entry_price,
            }
        )

    prompt = f"""
You are Aegis, an autonomous event-driven trading agent.

Analyze the following market event and the current portfolio.

MARKET EVENT:
Event type: {event.event_type}
Description: {event.description}
Sentiment: {event.sentiment}
Impact: {event.impact}
Affected assets: {event.affected_assets}

CURRENT OPEN POSITIONS:
{json.dumps(portfolio_context, indent=2)}

You must return ONLY valid JSON.

The JSON must contain exactly these fields:

{{
    "asset": "ticker symbol",
    "action": "BUY, SELL, or HOLD",
    "confidence": 0.0,
    "position_size": 0.0,
    "stop_loss": 0.0,
    "take_profit": 0.0,
    "reasoning": "brief explanation"
}}

STRICT RULES:

- action must be exactly BUY, SELL, or HOLD.
- asset must be one of the affected assets.
- confidence must be between 0.0 and 1.0.
- position_size must be between 0.0 and 0.10.
- stop_loss must be a POSITIVE decimal percentage.
- stop_loss must be greater than 0.0 and at most 0.20.
- take_profit must be a POSITIVE decimal percentage.
- take_profit must be greater than 0.0 and at most 0.50.
- Never return a negative stop_loss.
- Never return a negative take_profit.
- Example valid stop_loss: 0.03 means 3%.
- Example valid take_profit: 0.05 means 5%.

PORTFOLIO RULES:

- If an asset already has a LONG position, do not return BUY
  for that same asset.
- If an asset already has a SHORT position, do not return SELL
  for that same asset.
- If a current position conflicts with a strong new event,
  you may use the opposite action to close the position.
- A SELL against an existing LONG position means EXITING the LONG.
- A BUY against an existing SHORT position means COVERING the SHORT.
- Do not open a new position when the same asset already has
  an existing position unless the action is closing that position.
- Prefer HOLD when the event does not provide enough evidence
  for a new trade or position change.

POSITION MANAGEMENT:

- For a new BUY, use a positive position_size.
- For a new SELL short, use a positive position_size.
- For an exit of an existing position, use position_size = 1.0.
- For HOLD, position_size must be 0.0.
- For HOLD, stop_loss must be 0.0.
- For HOLD, take_profit must be 0.0.

RISK PARAMETERS:

- stop_loss must be greater than 0.0 for BUY or SELL.
- take_profit must be greater than 0.0 for BUY or SELL.
- take_profit should normally be greater than stop_loss.
- Keep the reasoning concise.
"""


    response = client.chat.completions.create(
        model="qwen3.8-max",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a disciplined autonomous trading "
                    "decision engine. Follow portfolio and numerical "
                    "constraints exactly."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    content = response.choices[0].message.content

    try:
        decision_data = json.loads(content)
    except json.JSONDecodeError:
        raise ValueError(
            f"Qwen returned invalid JSON:\n{content}"
        )

    required_fields = {
        "asset",
        "action",
        "confidence",
        "position_size",
        "stop_loss",
        "take_profit",
        "reasoning",
    }

    missing_fields = (
        required_fields - decision_data.keys()
    )

    if missing_fields:
        raise ValueError(
            f"Qwen response is missing fields: {missing_fields}"
        )

    action = str(
        decision_data["action"]
    ).upper()

    if action not in {
        "BUY",
        "SELL",
        "HOLD",
    }:
        raise ValueError(
            f"Invalid trading action returned by Qwen: {action}"
        )

    decision_data["action"] = action

    try:
        confidence = float(
            decision_data["confidence"]
        )

        position_size = float(
            decision_data["position_size"]
        )

        stop_loss = float(
            decision_data["stop_loss"]
        )

        take_profit = float(
            decision_data["take_profit"]
        )

    except (TypeError, ValueError):

        raise ValueError(
            "Qwen returned invalid numeric trading values."
        )

    if not 0.0 <= confidence <= 1.0:

        raise ValueError(
            f"Invalid confidence: {confidence}"
        )

    if not 0.0 <= position_size <= 1.0:

        raise ValueError(
            f"Invalid position size: {position_size}"
        )

    # --------------------------------
    # PORTFOLIO SAFETY VALIDATION
    # --------------------------------

    existing_position = current_positions.get(
        decision_data["asset"]
    )

    if existing_position:

        existing_side = existing_position.get(
            "side",
            "LONG",
        )

        # Existing LONG
        if existing_side == "LONG" and action == "BUY":

            raise ValueError(
                f"Qwen attempted to BUY {decision_data['asset']} "
                "while a LONG position already exists."
            )

        # Existing SHORT
        if existing_side == "SHORT" and action == "SELL":

            raise ValueError(
                f"Qwen attempted to SHORT {decision_data['asset']} "
                "while a SHORT position already exists."
            )

    # --------------------------------
    # HOLD
    # --------------------------------

    if action == "HOLD":

        decision_data["position_size"] = 0.0
        decision_data["stop_loss"] = 0.0
        decision_data["take_profit"] = 0.0

    # --------------------------------
    # TRADE
    # --------------------------------

    else:

        if stop_loss <= 0.0:

            raise ValueError(
                f"Invalid stop loss returned by Qwen: {stop_loss}"
            )

        if stop_loss > 0.20:

            raise ValueError(
                f"Stop loss is too large: {stop_loss}"
            )

        if take_profit <= 0.0:

            raise ValueError(
                f"Invalid take profit returned by Qwen: "
                f"{take_profit}"
            )

        if take_profit > 0.50:

            raise ValueError(
                f"Take profit is too large: {take_profit}"
            )

        decision_data["position_size"] = (
            position_size
        )

        decision_data["stop_loss"] = (
            stop_loss
        )

        decision_data["take_profit"] = (
            take_profit
        )

    decision_data["confidence"] = confidence

    return TradeDecision(
        **decision_data
    )


def classify_news(
    title: str,
    summary: str,
) -> MarketEvent:

    prompt = f"""
You are the event-detection system for Aegis,
an autonomous event-driven trading agent.

Analyze this financial news article.

TITLE:
{title}

SUMMARY:
{summary}

Determine whether this article represents a meaningful
market event.

Return ONLY valid JSON with exactly these fields:

{{
    "event_type": "EARNINGS, M&A, LEGAL, PRODUCT, MACRO, MANAGEMENT, GUIDANCE, OTHER",
    "description": "concise description of the market event",
    "sentiment": "POSITIVE, NEGATIVE, or NEUTRAL",
    "impact": "LOW, MEDIUM, or HIGH",
    "affected_assets": ["ticker symbols"]
}}

Rules:

- Only include assets genuinely affected by the event.
- Use an empty list if no specific public asset can be identified.
- Do not invent ticker symbols.
- Keep the description concise.
"""


    response = client.chat.completions.create(
        model="qwen3.8-max",
        messages=[
            {
                "role": "system",
                "content": (
                    "You identify and classify market-moving "
                    "events. Return only valid JSON."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    content = response.choices[0].message.content

    try:
        event_data = json.loads(content)

    except json.JSONDecodeError:

        raise ValueError(
            f"Qwen returned invalid JSON:\n{content}"
        )

    return MarketEvent(
        **event_data
    )