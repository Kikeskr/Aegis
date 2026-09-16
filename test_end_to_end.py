from agent.event_loop import EventLoop


print("=" * 70)
print("AEGIS FINAL END-TO-END TEST")
print("=" * 70)

aegis = EventLoop()


# --------------------------------------------------
# SHOW INITIAL STATE
# --------------------------------------------------

print("\nINITIAL ACCOUNT STATE")
print("-" * 70)

aegis.display_account()


# --------------------------------------------------
# CREATE A FRESH SYNTHETIC MARKET EVENT
# --------------------------------------------------

article = {
    "title": (
        "NVIDIA announces major new AI infrastructure "
        "partnership with leading technology companies"
    ),
    "summary": (
        "NVIDIA announces a significant expansion in AI "
        "infrastructure demand, with a new partnership "
        "expected to increase demand for its products."
    ),
    "url": (
        "https://aegis-final-test.local/"
        "nvidia-ai-partnership-test-001"
    ),
    "published": "2026-09-16",
}


# --------------------------------------------------
# PROCESS EVENT
# --------------------------------------------------

print("\nPROCESSING FRESH MARKET EVENT")
print("-" * 70)

try:
    aegis.process_article(article)

except Exception as error:

    print("\nEND-TO-END TEST ERROR")
    print("-" * 70)
    print(type(error).__name__)
    print(error)


# --------------------------------------------------
# FINAL ACCOUNT STATE
# --------------------------------------------------

print("\nFINAL ACCOUNT STATE")
print("-" * 70)

aegis.display_account()


# --------------------------------------------------
# PERFORMANCE
# --------------------------------------------------

print("\nFINAL PERFORMANCE")
print("-" * 70)

aegis.display_performance()


# --------------------------------------------------
# JOURNAL
# --------------------------------------------------

print("\nFINAL JOURNAL")
print("-" * 70)

aegis.display_journal()


# --------------------------------------------------
# TEST SUMMARY
# --------------------------------------------------

print("\n" + "=" * 70)
print("AEGIS END-TO-END TEST COMPLETE")
print("=" * 70)

print("\nPipeline tested:")

print("""
Market Event
    ↓
Event Classification
    ↓
Event Filter
    ↓
Qwen Analysis
    ↓
Portfolio Awareness
    ↓
Risk Engine
    ↓
Paper Execution
    ↓
Equity Recording
    ↓
Trade Journal
    ↓
Performance Metrics
""")

print("If no unhandled exception occurred, the pipeline completed.")