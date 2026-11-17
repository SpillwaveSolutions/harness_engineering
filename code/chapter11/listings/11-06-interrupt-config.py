interrupt_config = {
    "book_flight": {
        "allowed_decisions": ["approve", "edit", "reject"],  # full control
    },
    "search_flights": False,  # read-only, no interrupt
}
# Checkpointer is required for interrupt persistence
