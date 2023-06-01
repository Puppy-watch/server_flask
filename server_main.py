from flask import Flask, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_session import Session
import mysql.connector
from db_key import db
import datetime


column_list = ['stand', 'sleep', 'seat', 'walk', 'slowWalk', 'run', 'eat', 'bite']

app = Flask(__name__)

# Flask-Session 설정
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = 'asdfasdfasdfqwerty-puppy'
Session(app)

def get_dog_idx(user_idx):
    try:
        cursor = db.cursor()

        # 사용자의 강아지 인덱스 검색
        query = "SELECT dog_idx FROM dog WHERE user_idx=%s"
        cursor.execute(query, (user_idx,))
        dog = cursor.fetchone()

        if dog:
            return dog[0]
        else:
            return None
    except mysql.connector.Error as error:
        # 예외 처리: 강아지 인덱스를 찾을 수 없는 경우
        return None


# 회원가입 엔드포인트
@app.route('/signup', methods=['POST'])
def signup():
    # 요청에서 필요한 정보 추출
    data = request.json
    userId = data.get('userId')
    userPw = data.get('userPw')
    userName = data.get('userName')
    dogName = 'tempName'

    # 필수 정보가 비어있는지 확인
    if not userId or not userPw or not userName:
        return jsonify({'code': 400, 'error': 'User ID, PW, User name and dog name are required.'}), 400

    try:
        cursor = db.cursor()

        # 이미 등록된 사용자인지 확인
        query = "SELECT * FROM user WHERE userID=%s"
        cursor.execute(query, (userId,))
        user = cursor.fetchone()

        if user:
            return {'code': 401, 'error': 'User ID is already registered.'}, 401

        # 데이터베이스에 회원 정보 저장
        hashed_pw = generate_password_hash(userPw)
        insert_query = "INSERT INTO user (userID, userPw, userName) VALUES (%s, %s, %s);"
        cursor.execute(insert_query, (userId, hashed_pw, userName))
        db.commit()
        user_idx = cursor.lastrowid
        insert_query2 = "INSERT INTO dog (user_idx, dogName) VALUES (%s, %s);"
        cursor.execute(insert_query2, (user_idx, dogName))
        db.commit()
        dog_idx = cursor.lastrowid
        cursor.close()

        # 세션에 사용자 정보 저장
        session['user_idx'] = user_idx
        session['dog_idx'] = dog_idx

        response = {
            'code': 200,
            'message': 'User created successfully.',
            'userIdx': user_idx
        }

        return jsonify(response), 200
    except mysql.connector.Error as error:
        return jsonify({'code': 500, 'error': 'Failed to signup.', 'details': str(error)}), 500

# ID 확인 엔드포인트
@app.route('/checkId', methods=['POST'])
def check_ID():
    # 요청에서 필요한 정보 추출
    data = request.json
    userId = data.get('userId')

    # 필수 정보가 비어있는지 확인
    if not userId:
        return jsonify({'code': 400, 'error': 'User ID are required.'}), 400

    try:
        cursor = db.cursor()

        # 이미 등록된 사용자인지 확인
        query = "SELECT * FROM user WHERE userID=%s"
        cursor.execute(query, (userId,))
        user = cursor.fetchone()

        if user:
            return {'code': 401, 'error': 'User ID is already registered.'}, 401

        response = {
            'code': 200,
            'message': 'User ID is not registered.'
        }

        return jsonify(response), 200

    except mysql.connector.Error as error:
        return jsonify({'code': 500, 'error': 'Failed to check.', 'details': str(error)}), 500


# 로그인 엔드포인트
@app.route('/login', methods=['POST'])
def login():
    # 요청에서 필요한 정보 추출
    data = request.json
    userId = data.get('userId')
    userPw = data.get('userPw')

    try:
        cursor = db.cursor()

        # 사용자 확인
        query = "SELECT * FROM user WHERE userID=%s"
        cursor.execute(query, (userId,))
        user = cursor.fetchone()

        if not user or not check_password_hash(user[2], userPw):
            return {'code': 401, 'error': 'Invalid User ID or Password.'}, 401

        # 세션에 사용자 정보 저장
        session['user_idx'] = user[0]
        session['dog_idx'] = get_dog_idx(user[0])

        response = {
            'code': 200,
            'message': 'User login successfully.',
            'userIdx': user[0],
            'dogIdx': get_dog_idx(user[0])
        }

        return jsonify(response), 200
    except mysql.connector.Error as error:
        return jsonify({'code': 500, 'error': 'Failed to login.', 'details': str(error)}), 500

# 로그아웃 엔드포인트
@app.route('/logout', methods=['POST'])
def logout():
    # 세션에서 사용자 정보 삭제
    session.pop('user_idx', None)
    session.pop('dog_idx', None)
    return jsonify({'code': 200, 'message': 'User logout successfully.'}), 200


# 강아지 정보 수정 엔드포인트
@app.route('/dogs/<int:dog_idx>', methods=['PUT'])
def update_dog(dog_idx):
    data = request.get_json()

    # 요청 데이터에서 필요한 정보 추출
    dogName = data.get('dogName')
    dogAge = data.get('dogAge')
    dogWeight = data.get('dogWeight')
    firstTime = data.get('firstTime')
    secondTime = data.get('secondTime')
    thirdTime = data.get('thirdTime')

    try:
        # 세션에서 사용자 정보 확인
        # dog_idx = session.get('dog_idx')
        if dog_idx is None:
            return jsonify({'code': 401, 'error': 'dogIdx not found.'}), 401
            # return jsonify({'code': 401, 'error': 'User not logged in.'}), 401

        # 데이터베이스에서 사용자 정보 수정
        cursor = db.cursor()
        update_query = "UPDATE dog SET dogName = %s, dogAge = %s, dogWeight = %s, " \
                       "firstTime = %s, secondTime = %s, thirdTime = %s " \
                       "WHERE dog_idx = %s;"
        cursor.execute(update_query, (dogName, dogAge, dogWeight, firstTime, secondTime, thirdTime, dog_idx))
        db.commit()
        cursor.close()

        return jsonify({'code': 200, 'message': 'Dog updated successfully.'}), 200
    except mysql.connector.Error as error:
        return jsonify({'code': 500, 'error': 'Failed to update dog.', 'details': str(error)}), 500

# 현재 행동 정보를 반환하는 엔드포인트
@app.route('/dogs_info', methods=['GET'])
def get_dog_info():
    dog_idx = request.args.get('dog_idx')

    try:
        db.reconnect()
        if dog_idx is None:
            return jsonify({'code': 401, 'error': 'dogIdx not found.'}), 401

        # 데이터베이스에서 현재 행동 정보 가져오기
        cursor = db.cursor()
        select_query = "SELECT * FROM dog WHERE dog_idx = %s;"
        cursor.execute(select_query, (dog_idx, ))
        row = cursor.fetchone()
        cursor.close()

        # 현재 행동 정보를 반환
        behavior = {
            'code': 200,
            'message': 'Dog Info successfully.',
            'dogName': row[2],
            'dogAge': row[3],
            'dogWeight': row[4],
            'firstTime': row[5].strftime('%H:%M:%S'),
            'secondTime': row[6].strftime('%H:%M:%S'),
            'thirdTime': row[7].strftime('%H:%M:%S')
        }

        return jsonify(behavior), 200
    except mysql.connector.Error as error:
        return jsonify({'code': 500, 'error': 'Failed to find dog Info.', 'details': str(error)}), 500

# 현재 행동 정보를 반환하는 엔드포인트
@app.route('/behavior', methods=['GET'])
def get_now_behavior():
    dog_idx = request.args.get('dog_idx')

    try:
        db.reconnect()
        if dog_idx is None:
            return jsonify({'code': 401, 'error': 'dogIdx not found.'}), 401

        # 데이터베이스에서 현재 행동 정보 가져오기
        cursor = db.cursor()
        select_query = "SELECT * FROM behavior WHERE dog_idx = %s;"
        cursor.execute(select_query, (dog_idx, ))
        row = cursor.fetchone()
        cursor.close()

        # 현재 행동 정보를 반환
        behavior = {
            'code': 200,
            'message': 'NowBehavior successfully.',
            'nowBehav': column_list[int(row[2])]
        }

        return jsonify(behavior), 200
    except mysql.connector.Error as error:
        return jsonify({'code': 500, 'error': 'Failed to fetch abnormal.', 'details': str(error)}), 500


# 이상행동 정보를 반환하는 엔드포인트
@app.route('/abnormals', methods=['GET'])
def get_all_abnormals():
    dog_idx = request.args.get('dog_idx')

    try:
        # 세션에서 사용자 정보 확인
        # dog_idx = session.get('dog_idx')
        if dog_idx is None:
            return jsonify({'code': 401, 'error': 'dogIdx not found.'}), 401
            # return jsonify({'code': 401, 'error': 'User not logged in.'}), 401

        # 데이터베이스에서 모든 이상 행동 정보 가져오기
        cursor = db.cursor()
        select_query = "SELECT * FROM abnormal WHERE dog_idx = %s ORDER BY abnormalTime DESC;"
        cursor.execute(select_query, (dog_idx, ))
        rows = cursor.fetchall()
        cursor.close()

        # 이상 행동 정보를 반환
        adnormals = []
        for row in rows:
            adnormal = {
                'abnormalTime': row[3].strftime('%Y-%m-%d %H:%M:%S'),
                'abnormalName': row[2]
            }
            adnormals.append(adnormal)

        return jsonify({'code': 200, 'message': 'Abnormal List successfully.', 'data': adnormals}), 200
    except mysql.connector.Error as error:
        return jsonify({'code': 500, 'error': 'Failed to fetch abnormal.', 'details': str(error)}), 500


# 가장 많이 한 행동 정보를 반환하는 엔드포인트
@app.route('/mostBehav', methods=['GET'])
def get_mostBehav():
    # most_date = request.args.get('date')
    dog_idx = request.args.get('dog_idx')

    try:
        # 세션에서 사용자 정보 확인
        # dog_idx = session.get('dog_idx')
        if dog_idx is None:
            return jsonify({'code': 401, 'error': 'dogIdx not found.'}), 401

        # check_and_reconnect 함수 호출하여 연결 상태 확인 및 재연결
        check_and_reconnect()

        # 데이터베이스에서 해당하는 날짜의 행동 시간 정보 가져오기
        cursor = db.cursor()
        select_query = "SELECT * FROM mostBehavior where dogIdx = %s ORDER BY mDate DESC;"
        cursor.execute(select_query, (dog_idx, ))
        rows = cursor.fetchall()
        cursor.close()

        #가장 많이 한 행동
        mostBehav = []
        for row in rows:
            value = row[3:]
            max_idx = value.index(max(value))
            most = {
                'Date': row[2].strftime('%Y-%m-%d'),
                'mostBehav': column_list[max_idx]
            }
            mostBehav.append(most)

        most_json = {
            'code': 200,
            'message': 'MostBehavior successfully.',
            'data': mostBehav
        }

        return jsonify(most_json), 200
    except mysql.connector.Error as error:
        return jsonify({'code': 500, 'error': 'Failed to fetch mostBehavior.', 'details': str(error)}), 500


# 행동 통계 정보를 반환하는 엔드포인트
@app.route('/statistic', methods=['GET'])
def get_statistic_data():
    stat_date = request.args.get('date')
    dog_idx = request.args.get('dog_idx')

    try:
        # 세션에서 사용자 정보 확인
        # dog_idx = session.get('dog_idx')
        if dog_idx is None:
            return jsonify({'code': 401, 'error': 'dogIdx not found.'}), 401
            # return jsonify({'code': 401, 'error': 'User not logged in.'}), 401

        date = datetime.datetime.strptime(stat_date, '%Y-%m-%d').date()
        # 데이터베이스에서 해당하는 날짜의 행동 시간 정보 가져오기
        cursor = db.cursor()
        select_query = "SELECT * FROM mostBehavior where dogIdx = %s and mDate = %s;"
        cursor.execute(select_query, (dog_idx, date))
        row = cursor.fetchone()
        cursor.close()

        # 통계 정보를 반환
        statistic = {
            'code': 200,
            'message': 'Statistic data successfully.',
            'Date': stat_date,
            column_list[0]: int(row[3])//60,
            column_list[1]: int(row[4])//60,
            column_list[2]: int(row[5])//60,
            column_list[3]: int(row[6])//60,
            column_list[4]: int(row[7])//60,
            column_list[5]: int(row[8])//60,
            column_list[6]: int(row[9])//60,
            column_list[7]: int(row[10])//60
        }

        return jsonify(statistic), 200
    except mysql.connector.Error as error:
        return jsonify({'code': 500, 'error': 'Failed to fetch statistic.', 'details': str(error)}), 500

# RDS 연결 확인 및 재연결 함수
def check_and_reconnect():
    try:
        db.ping(reconnect=True)  # RDS 연결 상태 확인
        print('Connection to RDS is active')
    except mysql.connector.Error:
        print('Connection to RDS is lost. Reconnecting...')
        db.reconnect()  # RDS 재연결

# Flask 애플리케이션 실행 시 연결 확인 및 재연결 함수 호출
@app.before_request
def before_request():
    check_and_reconnect()
    #db.reconnect()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
