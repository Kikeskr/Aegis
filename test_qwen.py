from agent.event_loop import EventLoop


# Controlled test event.
# This is only being used to verify the full execution pipeline.

test_article = {
    "title": (
        "Apple reports quarterly earnings significantly "
        "above analyst expectations"
    ),
    "summary": (
        "Apple reports substantially stronger-than-expected "
        "quarterly revenue and earnings, raising expectations "
        "for near-term investor demand."
    ),
}


# Start Aegis

aegis = EventLoop()


# Process the event

aegis.process_article(
    article=test_article,
)


# Display journal

print("\n" + "=" * 60)
print("AEGIS TRADE JOURNAL")
print("=" * 60)

aegis.journal.show()