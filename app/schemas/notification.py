from pydantic import BaseModel

class PushNotificationRequest(BaseModel):
    title: str
    body: str
    topic: str
    data_payload: dict = {}

class BroadcastRequest(BaseModel):
    title: str
    body: str