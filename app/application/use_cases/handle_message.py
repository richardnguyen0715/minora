from loguru import logger

from app.application.interfaces.messenger import Messenger
from app.domain.entities.message import Message
from app.domain.services.message_service import MessageService


class HandleMessageUseCase:
    """
    Use case for handling incoming messages.

    Orchestrates the workflow: receive message → generate reply → send response.
    """

    def __init__(self, messenger: Messenger) -> None:
        """
        Initialize the use case with a messenger implementation.

        Args:
            messenger (Messenger): The messenger interface implementation.
        """
        self.messenger = messenger

    async def execute(self, message: Message) -> None:
        """
        Execute the message handling workflow.

        Args:
            message (Message): The normalized message to handle.
        """
        logger.info(
            "Processing message",
            extra={
                "chat_id": message.chat_id,
                "user_id": message.user_id,
                "type": message.type.value,
            },
        )

        reply = MessageService.generate_reply(message)

        logger.debug(
            "Generated reply",
            extra={"chat_id": message.chat_id, "reply": reply},
        )

        await self.messenger.send(message.chat_id, reply)

        logger.info(
            "Message processed successfully",
            extra={"chat_id": message.chat_id},
        )
