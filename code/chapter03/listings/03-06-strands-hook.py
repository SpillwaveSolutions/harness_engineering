from strands.hooks import BeforeToolCallEvent, HookProvider, HookRegistry


class BookingRulesHook(HookProvider):
    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(BeforeToolCallEvent, self.validate_booking)

    def validate_booking(self, event: BeforeToolCallEvent) -> None:
        if event.tool_use.get("name") != "book_flight":
            return
        passenger_count = event.tool_use.get("input", {}).get("passenger_count", 1)
        if passenger_count > 10:
            event.cancel_tool = (
                "BLOCKED: maximum passenger limit is 10, "
                f"received {passenger_count}."
            )


def main() -> None:
    from types import SimpleNamespace

    hook = BookingRulesHook()
    event = SimpleNamespace(
        tool_use={
            "name": "book_flight",
            "input": {"passenger_count": 11},
        },
        cancel_tool=False,
    )
    hook.validate_booking(event)
    print(event.cancel_tool)


if __name__ == "__main__":
    main()
