class CompleteOrderCommand:
    command_name = "CompleteOrderCommand"

    def __init__(
        self,
        operator_id: int,
        order_id: int,
        idempotency_key: str,
        completed_by: str,
        source: str = "API",
        notify_email: bool = True,
        notify_push: bool = True,
        note: str | None = None,
    ):
        self.operator_id = operator_id
        self.order_id = order_id
        self.idempotency_key = idempotency_key
        self.completed_by = completed_by
        self.source = source
        self.notify_email = notify_email
        self.notify_push = notify_push
        self.note = note
