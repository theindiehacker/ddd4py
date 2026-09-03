import abc


class NotificationPublisher(abc.ABC):
    """outbox に溜まった未発行の通知を MQ へ発行する (transactional outbox の publisher 側)。"""

    @abc.abstractmethod
    def publish_notifications(self) -> None:
        pass
