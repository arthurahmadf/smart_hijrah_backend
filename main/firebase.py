import firebase_admin
from firebase_admin import credentials
from django.conf import settings

_app = None

def init_firebase():
    global _app
    if _app is None:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIAL_PATH)
        _app = firebase_admin.initialize_app(cred)
    return _app
