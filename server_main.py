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
    dogName = data.get('dogName')

    # 필수 정보가 비어있는지 확인
    if not userId or not userPw or not userName or not dogName:
        return jsonify({'error': 'User ID, PW, User name and dog name are required.'}), 400

    try:
        cursor = db.cursor()

        # 이미 등록된 사용자인지 확인
        query = "SELECT * FROM user WHERE userID=%s"
        cursor.execute(query, (userId,))
        user = cursor.fetchone()

        if user:
            return {'error': 'User ID is already registered.'}, 401

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
            'message': 'User created successfully.',
            'user idx': user_idx,
            'dog idx': dog_idx
        }

        return jsonify(response), 201
    except mysql.connector.Error as error:
        return jsonify({'error': 'Failed to signup.', 'details': str(error)}), 500

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
            return {'error': 'Invalid username or password.'}, 401

        # 세션에 사용자 정보 저장
        session['user_idx'] = user[0]
        session['dog_idx'] = get_dog_idx(user[0])

        response = {
            'message': 'User login successfully.',
            'user idx': user[0],
            'dog idx': get_dog_idx(user[0])
        }

        return jsonify(response), 200
    except mysql.connector.Error as error:
        return jsonify({'error': 'Failed to login.', 'details': str(error)}), 500

# 로그아웃 엔드포인트
@app.route('/logout', methods=['POST'])
def logout():
    # 세션에서 사용자 정보 삭제
    session.pop('user_idx', None)
    session.pop('dog_idx', None)
    return jsonify({'message': 'User logout successfully.'}), 200


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
        user_idx = session.get('user_idx')
        if user_idx is None:
            return jsonify({'error': 'User not logged in.'}), 401

        # 데이터베이스에서 사용자 정보 수정
        cursor = db.cursor()
        update_query = "UPDATE dog SET dogName = %s, dogAge = %s, dogWeight = %s, " \
                       "firstTime = %s, secondTime = %s, thirdTime = %s " \
                       "WHERE dog_idx = %s;"
        cursor.execute(update_query, (dogName, dogAge, dogWeight, firstTime, secondTime, thirdTime, dog_idx))
        db.commit()
        cursor.close()

        return jsonify({'message': 'Dog updated successfully.'})
    except mysql.connector.Error as error:
        return jsonify({'error': 'Failed to update dog.', 'details': str(error)}), 500


# 현재 행동 정보를 반환하는 엔드포인트
@app.route('/behavior', methods=['GET'])
def get_now_behavior():
    try:
        # 세션에서 사용자 정보 확인
        dog_idx = session.get('dog_idx')
        if dog_idx is None:
            return jsonify({'error': 'User not logged in.'}), 401

        # 데이터베이스에서 현재 행동 정보 가져오기
        cursor = db.cursor()
        select_query = "SELECT * FROM behavior WHERE dog_idx = %s;"
        cursor.execute(select_query, (dog_idx, ))
        row = cursor.fetchone()
        cursor.close()

        # 현재 행동 정보를 반환
        behavior = {
            'nowBehav': row[3]
        }

        return jsonify(behavior)
    except mysql.connector.Error as error:
        return jsonify({'error': 'Failed to fetch abnormal.', 'details': str(error)}), 500


# 이상행동 정보를 반환하는 엔드포인트
@app.route('/abnormals', methods=['GET'])
def get_all_abnormals():
    try:
        # 세션에서 사용자 정보 확인
        dog_idx = session.get('dog_idx')
        if dog_idx is None:
            return jsonify({'error': 'User not logged in.'}), 401

        # 데이터베이스에서 모든 이상 행동 정보 가져오기
        cursor = db.cursor()
        select_query = "SELECT * FROM abnormal WHERE dog_idx = %s;"
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

        return jsonify(adnormals)
    except mysql.connector.Error as error:
        return jsonify({'error': 'Failed to fetch abnormal.', 'details': str(error)}), 500


# 가장 많이 한 행동 정보를 반환하는 엔드포인트
@app.route('/mostBehav', methods=['GET'])
def get_mostBehav():
    most_date = request.args.get('date')

    try:
        # 세션에서 사용자 정보 확인
        dog_idx = session.get('dog_idx')
        if dog_idx is None:
            return jsonify({'error': 'User not logged in.'}), 401

        date = datetime.datetime.strptime(most_date, '%Y-%m-%d').date()
        # 데이터베이스에서 해당하는 날짜의 행동 시간 정보 가져오기
        cursor = db.cursor()
        select_query = "SELECT * FROM mostBehavior where dogIdx = %s and mDate = %s;"
        cursor.execute(select_query, (dog_idx, date))
        row = cursor.fetchone()
        cursor.close()

        # 통계 정보를 반환
        value = row[3:]
        max_idx = value.index(max(value))
        most = {
            'Date': most_date,
            'mostBehav': column_list[max_idx + 3]
        }

        return jsonify(most)
    except mysql.connector.Error as error:
        return jsonify({'error': 'Failed to fetch mostBehavior.', 'details': str(error)}), 500


# 행동 통계 정보를 반환하는 엔드포인트
@app.route('/statistic', methods=['GET'])
def get_statistic_data():
    stat_date = request.args.get('date')

    try:
        # 세션에서 사용자 정보 확인
        dog_idx = session.get('dog_idx')
        if dog_idx is None:
            return jsonify({'error': 'User not logged in.'}), 401

        date = datetime.datetime.strptime(stat_date, '%Y-%m-%d').date()
        # 데이터베이스에서 해당하는 날짜의 행동 시간 정보 가져오기
        cursor = db.cursor()
        select_query = "SELECT * FROM mostBehavior where dogIdx = %s and mDate = %s;"
        cursor.execute(select_query, (dog_idx, date))
        row = cursor.fetchone()
        cursor.close()

        # 통계 정보를 반환
        statistic = {
            'Date': stat_date,
            column_list[0]: row[3],
            column_list[1]: row[4],
            column_list[2]: row[5],
            column_list[3]: row[6],
            column_list[4]: row[7],
            column_list[5]: row[8],
            column_list[6]: row[9],
            column_list[7]: row[10]
        }

        return jsonify(statistic)
    except mysql.connector.Error as error:
        return jsonify({'error': 'Failed to fetch statistic.', 'details': str(error)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
