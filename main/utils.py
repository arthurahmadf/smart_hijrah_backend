import firebase_admin
from firebase_admin import credentials, messaging
from project_management.firebase_config import firebase_admin

cred = credentials.Certificate("ssm-project-management-firebase-adminsdk-fbsvc-68d8de333e.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

def send_push_notification(token, title, body, data=None):
    message = messaging.Message(
        token=token,
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data or {},
    )

    response = messaging.send(message)
    return response
