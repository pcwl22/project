
from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
from flask_cors import CORS
import bcrypt
from datetime import datetime

app = Flask(__name__)
CORS(app)

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '202217'
app.config['MYSQL_DB'] = 'ultralytics_auth'

mysql = MySQL(app)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    password = data['password']  # 直接使用明文密码
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO users(username, password, created_at) VALUES(%s, %s, %s)", (username, password, created_at))
    mysql.connection.commit()
    cur.close()
    
    return jsonify({'message': '注册成功！'})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']  # 直接使用明文密码
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s", [username])
    user = cur.fetchone()
    cur.close()
    
    if not user:
        return jsonify({'message': '用户名或密码错误！'}), 401

    # user[2] is the password column
    stored_password = user[2]

    # 直接比对明文密码
    if password == stored_password:
        return jsonify({'message': '登录成功！'})
    else:
        return jsonify({'message': '用户名或密码错误！'}), 401

if __name__ == '__main__':
    app.run(debug=True)
