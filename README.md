# Aegis

## Autonomous Event-Driven AI Trading Agent

Aegis is an autonomous, event-driven AI trading agent that monitors market news, interprets market events using Qwen, generates structured trading decisions, applies portfolio-aware risk controls, and executes trades in a paper-trading environment.

The system is designed around an event → decision → risk → execution pipeline rather than continuous blind trading.

---

## Architecture

```text
Market News
     |
     v
RSS News Fetcher
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
     +------> Trade Journal
     |
     +------> Equity Curve
                    |
                    v
             Performance Engine
Core Features
Event-Driven Trading

Aegis reacts to market-moving news events rather than continuously generating random trade signals.

Events are classified by:

Event type
Description
Sentiment
Market impact
Affected assets
Qwen-Powered Market Analysis

Qwen analyzes validated market events and produces a structured trading decision.

Each decision contains:

Asset
Action
Confidence
Position size
Stop loss
Take profit
Reasoning

Supported actions:

BUY
SELL
HOLD
Portfolio Awareness

Aegis provides the current portfolio state to the AI before a trade decision is generated.

This helps prevent unnecessary duplicate exposure.

For example:

Existing position:

NVDA LONG

New event:

Positive NVDA news

Qwen decision:

HOLD

Instead of blindly opening another NVDA long position.

Risk Engine

Every AI decision passes through a dedicated risk layer before execution.

The risk engine controls:

Minimum AI confidence
Maximum position size
Maximum trade risk
Maximum stop-loss distance
Risk/reward ratio
Existing position conflicts
Full-position exits

Aegis separates AI reasoning from trade authorization.

The AI proposes.

The risk engine determines whether the proposal satisfies the configured risk rules.

Paper Trading

Aegis currently executes trades in a simulated portfolio.

The paper trader supports:

Long positions
Short positions
Position exits
Stop-loss
Take-profit
Realized P&L
Unrealized P&L
Portfolio equity tracking
Persistent account state

No live funds are required.

Event Memory

Processed news events are stored using their article URLs as event identifiers.

This prevents Aegis from repeatedly processing the same news article.

New article
     |
     v
Already processed?
    / \
  YES  NO
   |    |
 Skip  Process
Trade Journal

Trading decisions are recorded with:

Timestamp
Market event
Asset
Action
AI confidence
Position size
Stop loss
Take profit
AI reasoning
Risk decision
Execution result
Performance Tracking

Aegis tracks:

Total return
Maximum drawdown
Win rate
Sharpe ratio
Portfolio equity
Project Structure
aegis/
│
├── agent/
│   ├── event_filter.py
│   ├── event_loop.py
│   ├── event_memory.py
│   ├── events.py
│   ├── price_feed.py
│   ├── qwen_agent.py
│   ├── rss_news_fetcher.py
│   └── schemas.py
│
├── data/
│   ├── portfolio.json
│   ├── processed_events.json
│   └── trades.json
│
├── execution/
│   └── paper_trader.py
│
├── journal/
│   └── trade_journal.py
│
├── performance/
│   └── performance_engine.py
│
├── risk/
│   └── risk_engine.py
│
├── main.py
├── requirements.txt
├── test_end_to_end.py
├── test_paper_trader.py
├── test_performance.py
├── test_portfolio_awareness.py
├── test_qwen.py
└── test_risk_engine.py
Installation

Clone the repository:

git clone <YOUR_REPOSITORY_URL>
cd aegis

Create a virtual environment:

python -m venv .venv

Activate it on Windows Git Bash:

source .venv/Scripts/activate

Install dependencies:

pip install -r requirements.txt
Environment Variables

Create a .env file in the project root:

BITGET_QWEN_API_KEY=your_qwen_api_key

Never commit .env or API keys to GitHub.

Running Aegis

Start the autonomous agent:

python main.py

Aegis will continuously:

Fetch market news
Identify new events
Classify events
Filter low-value events
Ask Qwen for a structured decision
Check portfolio exposure
Apply risk controls
Execute approved decisions in paper trading
Monitor open positions
Record portfolio equity
Display performance metrics

Press:

CTRL+C

to stop the agent safely.

Testing

Compile the project:

python -m compileall agent execution journal performance risk main.py

Run the individual tests:

python test_paper_trader.py
python test_performance.py
python test_portfolio_awareness.py
python test_qwen.py
python test_risk_engine.py
python test_end_to_end.py
End-to-End Pipeline

The final integration test validates the complete Aegis workflow:

Market Event
     |
     v
Event Classification
     |
     v
Event Filter
     |
     v
Qwen Analysis
     |
     v
Portfolio Awareness
     |
     v
Risk Engine
     |
     v
Paper Execution
     |
     v
Equity Recording
     |
     v
Trade Journal
     |
     v
Performance Metrics

The pipeline has been tested successfully with a fresh synthetic market event.

The test demonstrated that a high-impact positive NVDA event was classified, filtered, analyzed by Qwen, evaluated against the existing portfolio, approved by the risk engine, and handled without opening an unnecessary duplicate NVDA position.

Risk Philosophy

Aegis follows a layered decision model:

AI proposes a trade
        |
        v
Portfolio checks exposure
        |
        v
Risk engine validates the proposal
        |
        v
Only approved decisions reach execution

This prevents the language model from having unrestricted control over trade execution.

The risk layer acts as a separate authorization boundary between AI reasoning and paper execution.

Current Scope

Aegis currently operates in a paper-trading environment.

The project focuses on demonstrating:

Autonomous event processing
AI-assisted market reasoning
Structured trading decisions
Portfolio-aware behavior
Risk-controlled execution
Automated performance tracking

Live trading is intentionally outside the current paper-trading demonstration scope.

Disclaimer

Aegis is an experimental software project and is not financial advice.

The current implementation uses simulated paper trading and simplified risk/performance models. It should not be used to trade real funds without substantial additional testing, validation, monitoring, and risk controls.