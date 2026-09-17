// ============================================================
// AEGIS FRONTEND
// ============================================================

let token =
    localStorage.getItem("aegis_token");

let currentUser = null;

let autoRefreshTimer = null;

let equityChart = null;


// ============================================================
// HELPERS
// ============================================================

function $(id) {
    return document.getElementById(id);
}


function money(value) {
    const number = Number(value || 0);

    return number.toLocaleString(
        "en-US",
        {
            style: "currency",
            currency: "USD",
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        }
    );
}


function pct(value) {
    const number = Number(value || 0);

    const sign =
        number > 0
            ? "+"
            : "";

    return `${sign}${number.toFixed(2)}%`;
}


function pctClass(value) {
    const number = Number(value || 0);

    if (number > 0) {
        return "positive";
    }

    if (number < 0) {
        return "negative";
    }

    return "";
}


function formatTime(value) {
    if (!value) {
        return "—";
    }

    const date =
        new Date(value);

    if (Number.isNaN(date.getTime())) {
        return "—";
    }

    return date.toLocaleString();
}


function escapeHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


// ============================================================
// API
// ============================================================

async function api(path, options = {}) {

    const headers = {
        ...(options.headers || {}),
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    };


    if (token) {
        headers.Authorization =
            `Bearer ${token}`;
    }


    if (
        options.body &&
        !headers["Content-Type"]
    ) {
        headers["Content-Type"] =
            "application/json";
    }


    const response =
        await fetch(path, {
            ...options,
            headers,
            cache: "no-store",
        });


    if (response.status === 401) {
        logout();

        throw new Error(
            "Session expired."
        );
    }


    const data =
        await response
            .json()
            .catch(() => ({}));


    if (!response.ok) {
        throw new Error(
            data.detail ||
            "Request failed."
        );
    }


    return data;
}


// ============================================================
// AUTH UI
// ============================================================

function showDashboard() {

    $("loginView")
        .classList
        .add("hidden");

    $("dashboardView")
        .classList
        .remove("hidden");
}


function showLogin() {

    $("dashboardView")
        .classList
        .add("hidden");

    $("loginView")
        .classList
        .remove("hidden");
}


function logout() {

    stopAutoRefresh();

    token = null;

    currentUser = null;

    localStorage.removeItem(
        "aegis_token"
    );

    showLogin();
}


// ============================================================
// LOGIN
// ============================================================

async function login(
    email,
    password
) {

    const data =
        await api(
            "/auth/login",
            {
                method: "POST",

                body: JSON.stringify({
                    email,
                    password,
                }),
            }
        );


    token =
        data.access_token;


    localStorage.setItem(
        "aegis_token",
        token
    );


    await initializeDashboard();
}


// ============================================================
// REGISTER
// ============================================================

async function register(
    username,
    email,
    password
) {

    await api(
        "/auth/register",
        {
            method: "POST",

            body: JSON.stringify({
                username,
                email,
                password,
            }),
        }
    );


    // Automatically log the new user in.
    await login(
        email,
        password
    );
}


// ============================================================
// INITIALIZE DASHBOARD
// ============================================================

async function initializeDashboard() {

    try {

        currentUser =
            await api("/auth/me");


        $("usernameLabel")
            .textContent =
            currentUser.username;


        $("emailLabel")
            .textContent =
            currentUser.email;


        $("userAvatar")
            .textContent =
            currentUser.username
                .charAt(0)
                .toUpperCase();


        showDashboard();


        await refreshOverview();


        startAutoRefresh();

    } catch (error) {

        logout();

        throw error;
    }
}


// ============================================================
// AUTOMATIC REFRESH
// ============================================================

function startAutoRefresh() {

    stopAutoRefresh();


    autoRefreshTimer =
        setInterval(
            async () => {

                if (!token) {
                    return;
                }


                try {

                    const timestamp =
                        Date.now();


                    const [
                        positions,
                        portfolio,
                        agentStatus,
                    ] =
                        await Promise.all([

                            api(
                                `/positions?_=${timestamp}`
                            ),

                            api(
                                `/portfolio?_=${timestamp}`
                            ),

                            loadAgentStatus(),

                        ]);


                    // ----------------------------------------
                    // POSITION COUNT
                    // ----------------------------------------

                    $("positionCount")
                        .textContent =
                        positions.length;


                    // ----------------------------------------
                    // OVERVIEW POSITIONS
                    // ----------------------------------------

                    renderPositionsTable(
                        positions,
                        $("overviewPositions")
                    );


                    // ----------------------------------------
                    // ACTIVE SECTION
                    // ----------------------------------------

                    const activeSection =
                        document.querySelector(
                            ".section:not(.hidden)"
                        );


                    // ----------------------------------------
                    // POSITIONS PAGE
                    // ----------------------------------------

                    if (
                        activeSection &&
                        activeSection.id ===
                            "positionsSection"
                    ) {

                        renderPositionsTable(
                            positions,
                            $("positionsTable")
                        );
                    }


                    // ----------------------------------------
                    // PORTFOLIO
                    // ----------------------------------------

                    renderPortfolio(
                        portfolio
                    );


                    // ----------------------------------------
                    // AGENT STATUS
                    // ----------------------------------------

                    renderAgentStatus(
                        agentStatus
                    );


                    // ----------------------------------------
                    // CURRENT SECTION DATA
                    // ----------------------------------------

                    if (
                        activeSection &&
                        activeSection.id ===
                            "tradesSection"
                    ) {

                        await loadTrades();

                    } else if (
                        activeSection &&
                        activeSection.id ===
                            "eventsSection"
                    ) {

                        await loadEvents();

                    } else if (
                        activeSection &&
                        activeSection.id ===
                            "performanceSection"
                    ) {

                        await loadPerformance();

                    } else if (
                        activeSection &&
                        activeSection.id ===
                            "overviewSection"
                    ) {

                        const [
                            trades,
                            events,
                        ] =
                            await Promise.all([

                                api(
                                    `/trades?_=${timestamp}`
                                ),

                                api(
                                    `/events?_=${timestamp}`
                                ),

                            ]);


                        $("tradeCount")
                            .textContent =
                            trades.length;


                        renderEvents(
                            events.slice(0, 5),
                            $("overviewEvents")
                        );
                    }

                } catch (error) {

                    console.error(
                        "Automatic refresh failed:",
                        error
                    );
                }

            },

            5_000
        );
}


function stopAutoRefresh() {

    if (autoRefreshTimer) {

        clearInterval(
            autoRefreshTimer
        );

        autoRefreshTimer = null;
    }
}


// ============================================================
// REFRESH CURRENT DATA
// ============================================================

async function refreshCurrentData() {

    const timestamp =
        Date.now();


    const [
        portfolio,
        positions,
        agentStatus,
    ] =
        await Promise.all([

            api(
                `/portfolio?_=${timestamp}`
            ),

            api(
                `/positions?_=${timestamp}`
            ),

            loadAgentStatus(),

        ]);


    renderPortfolio(
        portfolio
    );


    $("positionCount")
        .textContent =
        positions.length;


    renderPositionsTable(
        positions,
        $("overviewPositions")
    );


    renderAgentStatus(
        agentStatus
    );


    const activeSection =
        document.querySelector(
            ".section:not(.hidden)"
        );


    if (!activeSection) {
        return;
    }


    if (
        activeSection.id ===
        "tradesSection"
    ) {

        await loadTrades();

    } else if (
        activeSection.id ===
        "eventsSection"
    ) {

        await loadEvents();

    } else if (
        activeSection.id ===
        "positionsSection"
    ) {

        await loadPositions();

    } else if (
        activeSection.id ===
        "performanceSection"
    ) {

        await loadPerformance();

    } else if (
        activeSection.id ===
        "overviewSection"
    ) {

        const [
            trades,
            events,
        ] =
            await Promise.all([

                api(
                    `/trades?_=${timestamp}`
                ),

                api(
                    `/events?_=${timestamp}`
                ),

            ]);


        $("tradeCount")
            .textContent =
            trades.length;


        renderEvents(
            events.slice(0, 5),
            $("overviewEvents")
        );
    }
}


// ============================================================
// OVERVIEW
// ============================================================

async function refreshOverview() {

    const timestamp =
        Date.now();


    const [
        portfolio,
        positions,
        trades,
        events,
        agentStatus,
    ] =
        await Promise.all([

            api(
                `/portfolio?_=${timestamp}`
            ),

            api(
                `/positions?_=${timestamp}`
            ),

            api(
                `/trades?_=${timestamp}`
            ),

            api(
                `/events?_=${timestamp}`
            ),

            loadAgentStatus(),

        ]);


    renderPortfolio(
        portfolio
    );


    $("positionCount")
        .textContent =
        positions.length;


    $("tradeCount")
        .textContent =
        trades.length;


    renderPositionsTable(
        positions,
        $("overviewPositions")
    );


    renderEvents(
        events.slice(0, 5),
        $("overviewEvents")
    );


    renderAgentStatus(
        agentStatus
    );
}


// ============================================================
// PORTFOLIO
// ============================================================

function renderPortfolio(
    portfolio
) {

    $("totalEquity")
        .textContent =
        money(
            portfolio.total_equity
        );


    $("cashBalance")
        .textContent =
        money(
            portfolio.cash_balance
        );


    $("realizedPnl")
        .textContent =
        money(
            portfolio.realized_pnl
        );


    $("unrealizedPnl")
        .textContent =
        money(
            portfolio.unrealized_pnl
        );


    $("initialBalance")
        .textContent =
        money(
            portfolio.initial_balance
        );


    const returnEl =
        $("portfolioReturn");


    returnEl.textContent =
        pct(
            portfolio.return_pct
        );


    returnEl.className =
        `metric-change ${pctClass(
            portfolio.return_pct
        )}`;


    $("summaryReturn")
        .textContent =
        pct(
            portfolio.return_pct
        );


    $("summaryReturn").className =
        pctClass(
            portfolio.return_pct
        );


    if ($("chartCurrentEquity")) {

        $("chartCurrentEquity")
            .textContent =
            money(
                portfolio.total_equity
            );
    }


    if ($("chartReturn")) {

        $("chartReturn")
            .textContent =
            pct(
                portfolio.return_pct
            );


        $("chartReturn").className =
            pctClass(
                portfolio.return_pct
            );
    }
}


// ============================================================
// POSITIONS TABLE
// ============================================================

function renderPositionsTable(
    positions,
    container
) {

    if (!container) {
        return;
    }


    if (!positions.length) {

        container.innerHTML =
            `<div class="empty-state">
                No open positions.
            </div>`;

        return;
    }


    container.innerHTML = `

        <table>

            <thead>

                <tr>

                    <th>Asset</th>

                    <th>Side</th>

                    <th>Quantity</th>

                    <th>Entry</th>

                    <th>Current</th>

                    <th>P&L</th>

                    <th>Return</th>

                    <th>Stop</th>

                    <th>Target</th>

                    <th>Action</th>

                </tr>

            </thead>


            <tbody>

                ${positions.map(
                    position => `

                    <tr>

                        <td>

                            <strong>
                                ${escapeHtml(
                                    position.asset
                                )}
                            </strong>

                        </td>


                        <td>

                            <span
                                class="side-badge ${String(
                                    position.side || ""
                                ).toLowerCase()}"
                            >

                                ${escapeHtml(
                                    position.side
                                )}

                            </span>

                        </td>


                        <td>

                            ${Number(
                                position.quantity
                            ).toFixed(4)}

                        </td>


                        <td>

                            ${money(
                                position.entry_price
                            )}

                        </td>


                        <td>

                            ${money(
                                position.current_price
                            )}

                        </td>


                        <td
                            class="${pctClass(
                                position.unrealized_pnl
                            )}"
                        >

                            ${money(
                                position.unrealized_pnl
                            )}

                        </td>


                        <td
                            class="${pctClass(
                                position.return_pct
                            )}"
                        >

                            ${pct(
                                position.return_pct
                            )}

                        </td>


                        <td>

                            ${(
                                Number(
                                    position.stop_loss
                                ) * 100
                            ).toFixed(1)}%

                        </td>


                        <td>

                            ${(
                                Number(
                                    position.take_profit
                                ) * 100
                            ).toFixed(1)}%

                        </td>


                        <td>

                            <button
                                class="ghost-btn close-position-btn"
                                data-position-id="${position.id}"
                                data-asset="${escapeHtml(
                                    position.asset
                                )}"
                            >
                                Close
                            </button>

                        </td>

                    </tr>

                `
                ).join("")}

            </tbody>

        </table>

    `;


    document
        .querySelectorAll(
            ".close-position-btn"
        )
        .forEach(button => {

            button.addEventListener(
                "click",
                () => closePosition(
                    Number(
                        button.dataset.positionId
                    ),
                    button.dataset.asset
                )
            );

        });
}


// ============================================================
// MANUAL CLOSE POSITION
// ============================================================

async function closePosition(
    positionId,
    asset
) {

    const confirmed =
        window.confirm(
            `Close ${asset} position at the current market price?`
        );


    if (!confirmed) {
        return;
    }


    try {

        const button =
            document.querySelector(
                `[data-position-id="${positionId}"]`
            );


        if (button) {

            button.disabled = true;

            button.textContent =
                "Closing...";
        }


        const result =
            await api(
                `/positions/${positionId}/close`,
                {
                    method: "POST",
                }
            );


        alert(
            result.message
        );


        await refreshCurrentData();

    } catch (error) {

        alert(
            `Unable to close ${asset}: ${error.message}`
        );


        await refreshCurrentData();
    }
}


// ============================================================
// EVENTS
// ============================================================

function renderEvents(
    events,
    container
) {

    if (!container) {
        return;
    }


    if (!events.length) {

        container.innerHTML =
            `<div class="empty-state">
                No events recorded yet.
            </div>`;

        return;
    }


    container.innerHTML =
        events.map(event => {

            const decision =
                event.decision || {};


            const risk =
                event.risk || {};


            const execution =
                event.execution || {};


            const filterApproved =
                Boolean(
                    event.filter_approved
                );


            const riskApproved =
                Boolean(
                    risk.approved
                );


            const executed =
                Boolean(
                    execution.executed
                );


            const action =
                decision.action ||
                "NO DECISION";


            const confidence =
                decision.confidence != null
                    ? `${(
                        Number(
                            decision.confidence
                        ) * 100
                    ).toFixed(0)}%`
                    : "—";


            const filterText =
                filterApproved
                    ? "APPROVED"
                    : "REJECTED";


            const riskText =
                riskApproved
                    ? "APPROVED"
                    : risk
                        ? "REJECTED"
                        : "NOT REACHED";


            const executionText =
                executed
                    ? "EXECUTED"
                    : decision.action ===
                        "HOLD"
                        ? "HOLD"
                        : "NO TRADE";


            const filterClass =
                filterApproved
                    ? "pipeline-approved"
                    : "pipeline-rejected";


            const riskClass =
                riskApproved
                    ? "pipeline-approved"
                    : risk
                        ? "pipeline-rejected"
                        : "pipeline-neutral";


            const executionClass =
                executed
                    ? "pipeline-approved"
                    : decision.action ===
                        "HOLD"
                        ? "pipeline-neutral"
                        : "pipeline-rejected";


            const reasoning =
                decision.reasoning ||
                event.filter_reason ||
                "No reasoning recorded.";


            return `

                <article class="event-card">

                    <div class="event-header">

                        <div>

                            <div class="event-type">
                                ${escapeHtml(
                                    event.event_type
                                )}
                            </div>

                            <h4>
                                ${escapeHtml(
                                    event.description
                                )}
                            </h4>

                        </div>


                        <div class="event-time">

                            ${formatTime(
                                event.created_at
                            )}

                        </div>

                    </div>


                    <div class="event-meta">

                        <span>
                            Sentiment:
                            <strong>
                                ${escapeHtml(
                                    event.sentiment
                                )}
                            </strong>
                        </span>


                        <span>
                            Impact:
                            <strong>
                                ${escapeHtml(
                                    event.impact
                                )}
                            </strong>
                        </span>


                        <span>
                            Assets:
                            <strong>
                                ${escapeHtml(
                                    (
                                        event.affected_assets ||
                                        []
                                    ).join(", ") ||
                                    "None"
                                )}
                            </strong>
                        </span>

                    </div>


                    <div class="event-pipeline">

                        <div
                            class="pipeline-step ${filterClass}"
                        >

                            <span>
                                FILTER
                            </span>

                            <strong>
                                ${filterText}
                            </strong>

                        </div>


                        <div
                            class="pipeline-step ${riskClass}"
                        >

                            <span>
                                RISK
                            </span>

                            <strong>
                                ${riskText}
                            </strong>

                        </div>


                        <div
                            class="pipeline-step ${executionClass}"
                        >

                            <span>
                                EXECUTION
                            </span>

                            <strong>
                                ${executionText}
                            </strong>

                        </div>

                    </div>


                    <div class="event-decision">

                        <div>

                            <span>
                                AI Decision
                            </span>

                            <strong>
                                ${escapeHtml(
                                    action
                                )}
                            </strong>

                        </div>


                        <div>

                            <span>
                                Confidence
                            </span>

                            <strong>
                                ${confidence}
                            </strong>

                        </div>


                        <div>

                            <span>
                                Asset
                            </span>

                            <strong>
                                ${escapeHtml(
                                    decision.asset ||
                                    "—"
                                )}
                            </strong>

                        </div>

                    </div>


                    <div class="event-reasoning">

                        <strong>
                            AI Reasoning
                        </strong>


                        <div class="event-reasoning-text">

                            ${escapeHtml(
                                reasoning
                            )}

                        </div>

                    </div>


                    <div class="event-execution">

                        <strong>
                            Aegis Audit Trail
                        </strong>

                        — Event classified, evaluated by the
                        filter, passed through risk controls,
                        and execution status recorded.

                    </div>

                </article>

            `;

        }).join("");
}


// ============================================================
// LOAD EVENTS
// ============================================================

async function loadEvents() {

    const timestamp =
        Date.now();


    const events =
        await api(
            `/events?_=${timestamp}`
        );


    renderEvents(
        events,
        $("eventsList")
    );
}


// ============================================================
// LOAD TRADES
// ============================================================

async function loadTrades() {

    const timestamp =
        Date.now();


    const trades =
        await api(
            `/trades?_=${timestamp}`
        );


    const container =
        $("tradesTable");


    if (!trades.length) {

        container.innerHTML =
            `<div class="empty-state">
                No trades yet.
            </div>`;

        return;
    }


    container.innerHTML = `

        <table>

            <thead>

                <tr>

                    <th>Asset</th>

                    <th>Action</th>

                    <th>Side</th>

                    <th>Price</th>

                    <th>P&L</th>

                    <th>Return</th>

                    <th>Status</th>

                    <th>Time</th>

                </tr>

            </thead>


            <tbody>

                ${trades.map(
                    trade => `

                    <tr>

                        <td>

                            <strong>
                                ${escapeHtml(
                                    trade.asset
                                )}
                            </strong>

                        </td>


                        <td>
                            ${escapeHtml(
                                trade.action
                            )}
                        </td>


                        <td>
                            ${escapeHtml(
                                trade.side
                            )}
                        </td>


                        <td>
                            ${money(
                                trade.price
                            )}
                        </td>


                        <td
                            class="${pctClass(
                                trade.pnl
                            )}"
                        >

                            ${money(
                                trade.pnl
                            )}

                        </td>


                        <td
                            class="${pctClass(
                                trade.return_pct
                            )}"
                        >

                            ${pct(
                                trade.return_pct
                            )}

                        </td>


                        <td>

                            <span class="status-badge">

                                ${escapeHtml(
                                    trade.status
                                )}

                            </span>

                        </td>


                        <td>

                            ${formatTime(
                                trade.created_at
                            )}

                        </td>

                    </tr>

                `
                ).join("")}

            </tbody>

        </table>

    `;
}


// ============================================================
// LOAD POSITIONS
// ============================================================

async function loadPositions() {

    const timestamp =
        Date.now();


    const positions =
        await api(
            `/positions?_=${timestamp}`
        );


    renderPositionsTable(
        positions,
        $("positionsTable")
    );
}


// ============================================================
// PERFORMANCE
// ============================================================

async function loadPerformance() {

    const timestamp =
        Date.now();


    const [
        snapshots,
        portfolio,
    ] =
        await Promise.all([

            api(
                `/performance?_=${timestamp}`
            ),

            api(
                `/portfolio?_=${timestamp}`
            ),

        ]);


    $("chartCurrentEquity")
        .textContent =
        money(
            portfolio.total_equity
        );


    $("chartReturn")
        .textContent =
        pct(
            portfolio.return_pct
        );


    $("chartReturn").className =
        pctClass(
            portfolio.return_pct
        );


    const empty =
        $("chartEmpty");


    if (!snapshots.length) {

        empty.classList
            .remove("hidden");


        if (equityChart) {

            equityChart.destroy();

            equityChart = null;
        }


        return;
    }


    empty.classList
        .add("hidden");


    const labels =
        snapshots.map(
            snapshot =>
                new Date(
                    snapshot.created_at
                ).toLocaleTimeString()
        );


    const values =
        snapshots.map(
            snapshot =>
                Number(
                    snapshot.equity
                )
        );


    const canvas =
        $("equityChart");


    if (!canvas) {
        return;
    }


    if (equityChart) {

        equityChart.destroy();

        equityChart = null;
    }


    equityChart =
        new Chart(
            canvas,
            {
                type: "line",

                data: {
                    labels,

                    datasets: [
                        {
                            label: "Equity",

                            data: values,

                            tension: 0.25,

                            fill: false,
                        },
                    ],
                },

                options: {

                    responsive: true,

                    maintainAspectRatio: false,

                    plugins: {
                        legend: {
                            display: false,
                        },
                    },

                    scales: {

                        y: {
                            ticks: {
                                callback:
                                    value =>
                                        money(
                                            value
                                        ),
                            },
                        },

                    },

                },
            }
        );
}


// ============================================================
// AGENT STATUS
// ============================================================

async function loadAgentStatus() {

    const timestamp =
        Date.now();


    return await api(
        `/agent/status?_=${timestamp}`
    );
}


function renderAgentStatus(
    status
) {

    if (!status) {
        return;
    }


    const running =
        Boolean(
            status.running
        );


    if ($("agentCycles")) {

        $("agentCycles")
            .textContent =
            Number(
                status.cycles_completed ||
                0
            );
    }


    if ($("agentArticles")) {

        $("agentArticles")
            .textContent =
            Number(
                status.articles_fetched ||
                0
            );
    }


    if ($("agentNewEvents")) {

        $("agentNewEvents")
            .textContent =
            Number(
                status.new_events ||
                0
            );
    }


    if ($("agentRejected")) {

        $("agentRejected")
            .textContent =
            Number(
                status.events_rejected ||
                0
            );
    }


    if ($("agentDecisions")) {

        $("agentDecisions")
            .textContent =
            Number(
                status.ai_decisions ||
                0
            );
    }


    if ($("agentTrades")) {

        $("agentTrades")
            .textContent =
            Number(
                status.trades_executed ||
                0
            );
    }


    if ($("agentExits")) {

        $("agentExits")
            .textContent =
            Number(
                status.exits_triggered ||
                0
            );
    }


    if ($("agentLastEvent")) {

        $("agentLastEvent")
            .textContent =
            status.last_event_title ||
            "No event processed yet.";
    }


    if ($("agentLastEventTime")) {

        $("agentLastEventTime")
            .textContent =
            formatTime(
                status.last_event_time
            );
    }


    if ($("agentError")) {

        const error =
            status.last_error;


        $("agentError")
            .textContent =
            error
                ? `Last error: ${error}`
                : "No errors reported.";


        $("agentError").className =
            error
                ? "agent-error negative"
                : "agent-error";
    }


    const topStatus =
        document.querySelector(
            ".status-pill"
        );


    if (topStatus) {

        topStatus.classList.toggle(
            "agent-offline",
            !running
        );


        const label =
            topStatus.querySelector(
                ".status-label"
            );


        if (label) {

            label.textContent =
                running
                    ? "Aegis Online"
                    : "Aegis Offline";
        }
    }
}


// ============================================================
// SECTION NAVIGATION
// ============================================================

async function switchSection(
    section
) {

    document
        .querySelectorAll(".section")
        .forEach(
            sectionElement => {

                sectionElement
                    .classList
                    .add("hidden");

            }
        );


    const sectionElement =
        $(`${section}Section`);


    if (sectionElement) {

        sectionElement
            .classList
            .remove("hidden");
    }


    document
        .querySelectorAll(".nav-item")
        .forEach(item => {

            item.classList.toggle(
                "active",
                item.dataset.section ===
                    section
            );

        });


    const titles = {

        overview:
            "Overview",

        events:
            "Event Intelligence",

        trades:
            "Trades",

        positions:
            "Positions",

        performance:
            "Performance",

    };


    $("pageTitle")
        .textContent =
        titles[section] ||
        "Overview";


    if (section === "overview") {

        await refreshOverview();

    } else if (
        section === "events"
    ) {

        await loadEvents();

    } else if (
        section === "trades"
    ) {

        await loadTrades();

    } else if (
        section === "positions"
    ) {

        await loadPositions();

    } else if (
        section === "performance"
    ) {

        await loadPerformance();
    }
}


// ============================================================
// LOGIN FORM
// ============================================================

$("loginForm").addEventListener(
    "submit",
    async event => {

        event.preventDefault();


        $("loginError")
            .textContent =
            "";


        try {

            await login(
                $("email")
                    .value
                    .trim(),

                $("password")
                    .value
            );

        } catch (error) {

            $("loginError")
                .textContent =
                error.message;
        }
    }
);


// ============================================================
// REGISTER FORM
// ============================================================

$("registerForm").addEventListener(
    "submit",
    async event => {

        event.preventDefault();


        $("registerError")
            .textContent =
            "";


        const username =
            $("registerUsername")
                .value
                .trim();


        const email =
            $("registerEmail")
                .value
                .trim();


        const password =
            $("registerPassword")
                .value;


        const confirmPassword =
            $("registerConfirmPassword")
                .value;


        if (
            password !==
            confirmPassword
        ) {

            $("registerError")
                .textContent =
                "Passwords do not match.";

            return;
        }


        const button =
            $("registerForm")
                .querySelector(
                    'button[type="submit"]'
                );


        try {

            if (button) {

                button.disabled = true;

                button.textContent =
                    "Creating account...";
            }


            await register(
                username,
                email,
                password
            );

        } catch (error) {

            $("registerError")
                .textContent =
                error.message;

        } finally {

            if (button) {

                button.disabled = false;

                button.textContent =
                    "Create account";
            }
        }
    }
);


// ============================================================
// AUTH SWITCHING
// ============================================================

$("showRegisterBtn")
    .addEventListener(
        "click",
        () => {

            $("loginForm")
                .classList
                .add("hidden");


            $("registerForm")
                .classList
                .remove("hidden");


            $("registerError")
                .textContent =
                "";


            $("registerUsername")
                .focus();

        }
    );


$("showLoginBtn")
    .addEventListener(
        "click",
        () => {

            $("registerForm")
                .classList
                .add("hidden");


            $("loginForm")
                .classList
                .remove("hidden");


            $("loginError")
                .textContent =
                "";


            $("email")
                .focus();

        }
    );


// ============================================================
// LOGOUT
// ============================================================

$("logoutBtn")
    .addEventListener(
        "click",
        logout
    );


// ============================================================
// MANUAL REFRESH BUTTONS
// ============================================================

$("refreshBtn")
    .addEventListener(
        "click",
        refreshOverview
    );


$("eventsRefreshBtn")
    .addEventListener(
        "click",
        loadEvents
    );


$("tradesRefreshBtn")
    .addEventListener(
        "click",
        loadTrades
    );


$("positionsRefreshBtn")
    .addEventListener(
        "click",
        loadPositions
    );


$("performanceRefreshBtn")
    .addEventListener(
        "click",
        loadPerformance
    );


// ============================================================
// SIDEBAR NAVIGATION
// ============================================================

document
    .querySelectorAll(".nav-item")
    .forEach(item => {

        item.addEventListener(
            "click",
            () =>
                switchSection(
                    item.dataset.section
                )
        );

    });


// ============================================================
// VIEW ALL
// ============================================================

document
    .querySelectorAll("[data-go]")
    .forEach(button => {

        button.addEventListener(
            "click",
            () =>
                switchSection(
                    button.dataset.go
                )
        );

    });


// ============================================================
// REFRESH WHEN TAB BECOMES ACTIVE
// ============================================================

document.addEventListener(
    "visibilitychange",
    async () => {

        if (
            document.visibilityState ===
                "visible" &&
            token
        ) {

            try {

                await refreshCurrentData();

            } catch (error) {

                console.error(
                    "Visibility refresh failed:",
                    error
                );
            }
        }
    }
);


// ============================================================
// RESTORE SESSION
// ============================================================

if (token) {

    initializeDashboard()
        .catch(() => {
            logout();
        });

} else {

    showLogin();
}