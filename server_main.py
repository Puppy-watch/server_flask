from flask import Flask, request, jsonify
import mysql.connector
from db_key import db

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
    if not userId or not userPw:
        return jsonify({'error': 'Username and password are required.'}), 400

    try:
        # 데이터베이스에 회원 정보 저장
        cursor = db.cursor()
        insert_query = "INSERT INTO user (userID, userPw, userName) VALUES (%s, %s, %s);"
        cursor.execute(insert_query, (userId, userPw, userName))
        db.commit()
        user_idx = cursor.lastrowid
        insert_query = "INSERT INTO dog (user_idx, dogName) VALUES (%d, %s);"
        cursor.execute(insert_query, (user_idx, dogName))
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
    firstEat = data.get('firstEat')
    secondEat = data.get('secondEat')
    thirdEat = data.get('thirdEat')

    try:
        # 데이터베이스에서 사용자 정보 수정
        cursor = db.cursor()
        update_query = "UPDATE dog SET dogName = %s, dogAge = %d, dogWeight = %d, " \
                       "firstEat = %s, secondEat = %s, thirdEat = %s " \
                       "WHERE dog_idx = %d;"
        cursor.execute(update_query, (dogName, dogAge, dogWeight, firstEat, secondEat, thirdEat, dog_idx))
        db.commit()
        cursor.close()

        return jsonify({'message': 'User updated successfully.'})
    except mysql.connector.Error as error:
        return jsonify({'error': 'Failed to update user.', 'details': str(error)}), 500

# 이상행동 정보를 반환하는 엔드포인트
@app.route('/adnormal', methods=['GET'])
def get_all_users():
    try:
        # 데이터베이스에서 모든 사용자 정보 가져오기
        cursor = db.cursor()
        select_query = "SELECT * FROM abnormal"
        cursor.execute(select_query)
        rows = cursor.fetchall()
        cursor.close()

        # 사용자 정보를 리스트로 변환하여 반환
        users = []
        for row in rows:
            user = {
                'abnormalTime': row[3],
                'abnormalName': row[2]
            }
            users.append(user)

        return jsonify(users)
    except mysql.connector.Error as error:
        return jsonify({'error': 'Failed to fetch users.', 'details': str(error)}), 500



if __name__ == '__main__':
    app.run(debug=True)