from app.domain.entities.message import Message
from app.domain.enums.message_type import MessageType


class MessageService:
    """
    Service for processing messages and generating appropriate responses.

    This service contains the core business logic for message handling,
    independent of any framework or external system.
    """

    @staticmethod
    def generate_reply(message: Message) -> str:
        """
        Generate a reply text based on the received message type.

        Args:
            message (Message): The normalized message entity.

        Returns:
            str: The reply text to send back to the user.
        """
        if message.type == MessageType.TEXT:
            return "I have received your message."
        elif message.type == MessageType.MEDIA:
            return "I have received the content you sent."
        else:
            return "Empty message has been received."
