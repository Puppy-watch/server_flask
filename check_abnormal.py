import firebase_admin
from firebase_admin import credentials
from firebase_admin import messaging
import time
from db_key import db, TOKEN
import mysql.connector

# 파이어베이스 연결
cred = credentials.Certificate('service_key.json')
default_app = firebase_admin.initialize_app(cred)
print(default_app.name)  # "[DEFAULT]"

registration_token = TOKEN

# RDS 연결 확인 및 재연결 함수
def check_and_reconnect():
    try:
        db.ping(reconnect=True)  # RDS 연결 상태 확인
        print('Connection to RDS is active')
    except mysql.connector.Error:
        print('Connection to RDS is lost. Reconnecting...')
        db.reconnect()  # RDS 재연결


def check_database_changes():
    previous_state = None

    while True:
        try:
            print('start')
            print(previous_state)
            # db.disconnect()
            # time.sleep(2)
            # check_and_reconnect()
            db.reconnect()
            cursor = db.cursor()

            # abnormal 테이블의 변경 사항을 확인
            query = "SELECT abnorm_idx FROM abnormal ORDER BY abnorm_idx DESC LIMIT 1"
            cursor.execute(query)
            abnormal = cursor.fetchone()
            cursor.close()

            current_state = abnormal
            print(abnormal)

            # 변경 사항이 있을 경우, 알림을 보내는 로직을 실행합니다.
            if current_state != previous_state:
                print('detect')
                previous_state = current_state
                message = messaging.Message(
                    notification=messaging.Notification(
                        title="Puppy Watch",
                        body="이상행동 감지!"
                    ),
                    token=registration_token,
                )

                response = messaging.send(message)
                print('Successfully sent message:', response)
            else:
                pass

        except mysql.connector.Error as error:
            print("Error:", error)

        # 주기적으로 데이터베이스를 확인하기 위해 일정 시간 간격을 둡니다.
        time.sleep(30)  # 30초마다 데이터베이스를 확인합니다.

if __name__ == '__main__':
    check_database_changes()