from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash
from collections import OrderedDict
import mysql.connector
from db_key import db
import datetime

column_list = ['stand', 'sleep', 'seat', 'walk', 'slowWalk', 'run', 'eat', 'bite']

app = Flask(__name__)


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

        response = {
            'message': 'User created successfully.',
            'user idx': user_idx,
            'dog idx': dog_idx
        }

        return jsonify(response), 201
    except mysql.connector.Error as error:
        return jsonify({'error': 'Failed to signup.', 'details': str(error)}), 500


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
    dog_idx = request.args.get('dog_idx')
    try:
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
    dog_idx = request.args.get('dog_idx')
    try:
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
    dog_idx = request.args.get('dog_idx')
    most_date = request.args.get('date')

    try:
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
    dog_idx = request.args.get('dog_idx')
    stat_date = request.args.get('date')

    try:
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
