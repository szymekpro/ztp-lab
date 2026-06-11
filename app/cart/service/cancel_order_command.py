class CancelOrderCommand:
    command_name = "CancelOrderCommand"

    def __init__(
        self,
        operator_id: int,
        order_id: int,
        reason: str | None = None,
    ):
        self.operator_id = operator_id
        self.order_id = order_id
        self.reason = reason
