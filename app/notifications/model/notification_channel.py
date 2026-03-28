from enum import Enum


class NotificationChannel(str, Enum):
    EMAIL = "EMAIL"
    PUSH = "PUSH"
