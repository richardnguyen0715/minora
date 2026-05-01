import json

import redis.asyncio as redis
from loguru import logger

from app.application.interfaces.queue import Queue


class RedisQueue(Queue):
    """
    Queue implementation using Redis.

    Provides asynchronous message queuing for scalable message processing.
    """

    def __init__(self, redis_url: str, queue_name: str = "telegram_messages") -> None:
        """
        Initialize the Redis queue.

        Args:
            redis_url (str): Redis connection URL.
            queue_name (str): Name of the queue key in Redis.
        """
        self.redis_url = redis_url
        self.queue_name = queue_name
        self.redis_client = None

    async def connect(self) -> None:
        """Connect to Redis server."""
        self.redis_client = await redis.from_url(self.redis_url)
        logger.info(
            "Connected to Redis",
            extra={"url": self.redis_url, "queue": self.queue_name},
        )

    async def disconnect(self) -> None:
        """Disconnect from Redis server."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis")

    async def publish(self, event: dict) -> None:
        """
        Publish an event to the queue.

        Args:
            event (dict): The event payload to publish.
        """
        if not self.redis_client:
            await self.connect()

        serialized_event = json.dumps(event)
        await self.redis_client.rpush(self.queue_name, serialized_event)

        logger.debug(
            "Event published to queue",
            extra={"queue": self.queue_name, "event": event},
        )

    async def consume(self) -> dict:
        """
        Consume an event from the queue (blocking).

        Returns:
            dict: The consumed event payload.
        """
        if not self.redis_client:
            await self.connect()

        serialized_event = await self.redis_client.blpop(self.queue_name, timeout=0)

        if serialized_event:
            event = json.loads(serialized_event[1])
            logger.debug(
                "Event consumed from queue",
                extra={"queue": self.queue_name, "event": event},
            )
            return event

        return {}
