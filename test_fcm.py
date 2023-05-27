from pyfcm import FCMNotification
from db_key import APIKEY, TOKEN

# 파이어베이스 콘솔에서 얻어 온 서버 키를 넣어 준다
push_service = FCMNotification(APIKEY)

def sendMessage(body, title):
    # 토큰값을 이용해 1명에게 푸시알림을 전송함
    result = push_service.notify_single_device(registration_id=TOKEN, message_title=title, message_body=body, data_message=data_message)

    # 전송 결과 출력
    print(result)


sendMessage("제목입니다", "내용입니다!")