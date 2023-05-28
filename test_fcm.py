import firebase_admin
from firebase_admin import credentials
from firebase_admin import messaging
from db_key import TOKEN

cred = credentials.Certificate('service_key.json')
default_app = firebase_admin.initialize_app(cred)
print(default_app.name)  # "[DEFAULT]"

registration_token = TOKEN

message = messaging.Message(
    notification = messaging.Notification(
        title="예약타이틀",
        body="예약승인되었습니다.",
    ),
    token=registration_token,
)

response = messaging.send(message)
print('Successfully sent message:', response)
