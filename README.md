# Aegis

## Autonomous Event-Driven AI Trading Agent

Aegis is an autonomous, event-driven AI trading agent built for the Bitget AI × Crypto Hackathon.

Instead of continuously generating blind trading signals, Aegis monitors market news, identifies potentially market-moving events, uses Qwen to reason about those events, validates the proposed decision through an independent risk engine, and executes approved decisions in a persistent paper-trading environment.

The core principle is:

> Qwen proposes. Aegis Risk Engine authorizes. Paper Trader executes.

---

# What Aegis Does

Aegis continuously processes the following pipeline:

```text
Market News
     |
     v
News Ingestion
     |
     v
Event Classification
     |
     v
Event Filter
     |
     v
Qwen AI Analysis
     |
     v
Portfolio Awareness
     |
     v
Risk Engine
     |
     v
Paper Trader
     |
     v
Portfolio / P&L
     |
     v
Dashboard & Audit Trail

The system is event-driven and autonomous. Once running, the agent continuously monitors market information, processes new events, makes decisions, applies risk controls, executes approved paper trades, and monitors open positions.

Key Features
1. Event-Driven Market Intelligence

Aegis monitors market news across multiple assets and sources.

Current monitored assets include:

NVDA
AAPL
GOOGL
AMD
TSLA
MSFT
AMZN
META
SPY
QQQ

News articles are converted into structured market events containing:

Event type
Description
Sentiment
Market impact
Affected assets

Low-value or neutral events can be rejected before reaching the AI decision layer.

2. Qwen-Powered Trading Decisions

Aegis uses Qwen to analyze validated market events.

The AI produces a structured trading decision containing:

Asset
Action
Confidence
Position Size
Stop Loss
Take Profit
Reasoning

Supported actions:

BUY
SELL
HOLD

The AI is not given unrestricted control over execution.

Its output is treated as a proposal that must pass the risk layer.

3. Portfolio Awareness

Before generating a decision, Aegis provides the current portfolio state to the AI.

This allows the system to consider existing exposure.

For example:

Existing Position:
NVDA LONG

New Event:
Positive NVDA News

AI:
HOLD

Rather than blindly opening another position in the same direction.

Aegis also prevents duplicate same-side positions through its risk and execution layers.

4. Independent Risk Engine

Every AI decision passes through a dedicated risk engine before execution.

The risk engine validates:

Minimum AI confidence
Maximum position size
Maximum trade risk
Maximum stop-loss distance
Risk/reward ratio
Existing position conflicts
Exit position sizing
Invalid trading actions

The architecture deliberately separates AI reasoning from trade authorization.

Qwen
  |
  | proposes
  v
Risk Engine
  |
  | authorizes
  v
Paper Trader

This prevents the language model from having unrestricted authority over execution.

5. Autonomous Position Management

Aegis continuously monitors open positions.

Positions can be closed automatically when:

Stop-loss is reached
Take-profit is reached
An opposing AI decision results in an exit

A position can also be manually closed through the web dashboard.

Manual closure uses the same accounting path as automatic exits, ensuring that:

P&L is calculated
Return percentage is recorded
Wallet balance is updated
Realized P&L is updated
The trade is recorded
The position is removed
6. Paper Trading

Aegis currently operates entirely in a simulated trading environment.

Each user receives a paper portfolio with:

Initial Balance: $10,000

The paper trader supports:

Long positions
Short positions
Position exits
Stop-loss
Take-profit
Realized P&L
Unrealized P&L
Portfolio equity
Return percentage
Persistent trade history

No real funds are used.

7. Multi-User Web Dashboard

Aegis includes a FastAPI-powered web application.

Users can create accounts and receive their own paper portfolio.

The dashboard provides:

Overview
Event Intelligence
Trades
Positions
Performance
Agent Status

Users can view:

Current equity
Cash balance
Realized P&L
Unrealized P&L
Portfolio return
Open positions
Current market prices
Trade history
AI decisions
AI reasoning
Risk decisions
Execution results
Agent activity
Equity history

The dashboard automatically synchronizes with the backend.

8. Event Audit Trail

Every processed event can be recorded with its complete decision pipeline.

Aegis records:

Market Event
     |
     v
Filter Decision
     |
     v
AI Decision
     |
     v
Risk Decision
     |
     v
Execution Result
     |
     v
Portfolio Result

This makes the agent's decisions observable rather than treating the AI as a black box.

9. Event Memory

Processed news articles are tracked using their article URLs.

This prevents the same article from being repeatedly processed.

New Article
     |
     v
Already Processed?
    / \
  YES  NO
   |    |
 Skip  Process
10. Autonomous Worker

Once started, the autonomous worker continuously performs:

Monitor Existing Positions
          |
          v
Fetch Market News
          |
          v
Identify New Events
          |
          v
Filter Events
          |
          v
Ask Qwen for Decisions
          |
          v
Apply Risk Controls
          |
          v
Execute Approved Trades
          |
          v
Record Portfolio State

The worker operates independently of the dashboard.

The dashboard acts as the control and observability layer for the autonomous system.

11. Position Capacity Control

Aegis limits the number of concurrent open positions per user.

The configured maximum is:

5 open positions

When a user's portfolio reaches the configured capacity, the worker stops sourcing new opportunities for that portfolio until capacity becomes available again.

Existing positions continue to be monitored for exits.

Architecture
                    AEGIS
                      |
              Autonomous Worker
                      |
          +-----------+-----------+
          |                       |
          v                       v
     News Sources            Position Monitor
          |                       |
          v                       v
    Event Detection          SL / TP Checks
          |
          v
     Event Filter
          |
          v
       Qwen AI
          |
          v
  Portfolio Awareness
          |
          v
     Risk Engine
          |
          v
     Paper Trader
          |
     +----+----+
     |         |
     v         v
  Database   P&L
     |
     v
FastAPI Backend
     |
     v
Web Dashboard
Web Application Architecture
Browser
   |
   v
FastAPI
   |
   +----------------+
   |                |
   v                v
Authentication   Aegis Service
                     |
             +-------+-------+
             |       |       |
             v       v       v
           Qwen    Risk    Trader
             |       |       |
             +-------+-------+
                     |
                     v
                  SQLite
Technology Stack
Backend
Python
FastAPI
SQLAlchemy
SQLite
Pydantic
JWT authentication
AI
Qwen
Structured AI trading decisions
Market Data
Yahoo Finance
Google News RSS
Multi-asset news ingestion
Frontend
HTML
CSS
JavaScript
Chart.js
Trading
Custom paper-trading engine
Portfolio-aware execution
Stop-loss / take-profit monitoring
Persistent trade records
Project Structure
AEGIS/
|
├── agent/
│   ├── event_filter.py
│   ├── event_loop.py
│   ├── event_memory.py
│   ├── events.py
│   ├── price_feed.py
│   ├── qwen_agent.py
│   ├── rss_news_fetcher.py
│   ├── schemas.py
│   ├── database_event_memory.py
│   └── background_worker.py
|
├── api/
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── auth.py
│   ├── aegis_service.py
│   └── server.py
|
├── execution/
│   ├── paper_trader.py
│   └── database_paper_trader.py
|
├── risk/
│   └── risk_engine.py
|
├── performance/
│   └── performance_engine.py
|
├── journal/
│   └── trade_journal.py
|
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
|
├── data/
│   ├── portfolio.json
│   ├── processed_events.json
│   └── trades.json
|
├── main.py
└── README.md
Installation

Clone the repository:

git clone https://github.com/Kikeskr/Aegis.git
cd Aegis

Create a virtual environment:

python -m venv .venv

Activate it on Windows:

.venv\Scripts\activate

Install dependencies:

pip install -r requirements.txt
Environment Variables

Create a .env file in the project root:

BITGET_QWEN_API_KEY=your_qwen_api_key

Never commit .env or API keys to GitHub.

Running Aegis

Start the web application and autonomous engine:

python -m uvicorn api.server:app --reload

The application will be available at:

http://127.0.0.1:8000

The FastAPI startup process initializes the autonomous event engine.

Once running, Aegis continuously monitors market events and positions.

Autonomous Processing

A typical cycle looks like:

AEGIS AUTONOMOUS EVENT CYCLE
        |
        v
Position Monitor
        |
        v
Market News Fetch
        |
        v
New Market Event
        |
        v
Event Filter
        |
        v
Qwen Analysis
        |
        v
Risk Evaluation
        |
        v
Paper Execution
        |
        v
Portfolio Update
Price Monitoring

Aegis retrieves current market prices for open positions and uses them to calculate:

Current position value
Unrealized P&L
Return percentage
Stop-loss conditions
Take-profit conditions
Portfolio equity

The dashboard automatically refreshes portfolio and position data.

Authentication

Users can:

Create Account
      |
      v
Receive $10,000 Paper Wallet
      |
      v
Automatically Sign In
      |
      v
Access Personal Dashboard

Each portfolio is associated with its authenticated user.

Position and portfolio operations are scoped to the user's own paper wallet.

Risk Philosophy

Aegis follows a layered authorization model:

             AI
              |
              | proposes
              v
        Portfolio State
              |
              v
         Risk Engine
              |
              | authorizes
              v
        Paper Trader

The AI is responsible for market reasoning.

The risk engine is responsible for enforcing configured trading constraints.

The paper trader is responsible for execution and accounting.

This separation creates a clear boundary between AI reasoning and execution.

Testing

Compile the project:

python -m compileall agent api execution journal performance risk main.py

Run the available tests individually where applicable:

python test_paper_trader.py
python test_performance.py
python test_portfolio_awareness.py
python test_qwen.py
python test_risk_engine.py
python test_end_to_end.py

The system has also been tested through the live autonomous pipeline, including:

News ingestion
Event filtering
Qwen analysis
Risk validation
Paper execution
Portfolio updates
Position monitoring
Automatic exits
Manual position closing
Dashboard synchronization
Multi-user paper portfolios
Demonstrated Workflow

Aegis has demonstrated the complete event-driven workflow:

Market News
     |
     v
New Event
     |
     v
Event Filter
     |
     v
Qwen Decision
     |
     v
Risk Validation
     |
     v
Paper Execution
     |
     v
Open Position
     |
     v
Live Price Monitoring
     |
     v
Exit
     |
     v
Realized P&L

The web dashboard exposes this process so that users can observe what the autonomous agent is doing.

Current Scope

Aegis is currently a paper-trading system designed to demonstrate autonomous event-driven AI trading.

The project focuses on:

Autonomous event processing
AI-assisted market reasoning
Structured trading decisions
Portfolio-aware behavior
Independent risk authorization
Automated paper execution
Position monitoring
Automated exits
Performance tracking
Multi-user paper portfolios
Transparent decision auditing

Live-money trading is intentionally outside the current demonstration scope.

Security & Safety

Aegis does not use real trading funds.

API credentials must remain outside the repository.

The current system is an experimental software project and should not be used for real-money trading without substantial additional development, testing, security review, market-data validation, execution safeguards, monitoring, and risk controls.

Hackathon Context

Aegis was developed for the:

Bitget AI × Crypto Hackathon — Build What Trades Next

The project focuses on the Agentic Trading / Event-Driven Agent concept.

The system demonstrates how an AI agent can:

Sense
  ↓
Interpret
  ↓
Reason
  ↓
Check Risk
  ↓
Act
  ↓
Observe
  ↓
Manage

Rather than simply generating trading predictions, Aegis demonstrates an autonomous decision pipeline connecting market events, AI reasoning, risk authorization, execution, and portfolio management.

License

This project is provided for experimental and educational purposes.