from abc import ABC, abstractmethod


class Queue(ABC):
    """
    Abstract interface for message queuing systems.

    Enables decoupling of message reception from processing,
    supporting scalable and resilient message handling.
    """

    @abstractmethod
    async def publish(self, event: dict) -> None:
        """
        Publish an event to the queue.

        Args:
            event (dict): The event payload to publish.

        Raises:
            Exception: If the event cannot be published.
        """
        pass

    @abstractmethod
    async def consume(self) -> dict:
        """
        Consume an event from the queue.

        Returns:
            dict: The consumed event payload.

        Raises:
            Exception: If no event can be consumed.
        """
        pass
