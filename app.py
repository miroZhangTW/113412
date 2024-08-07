from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# 模擬資料庫
users = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['newUsername']
    password = request.form['newPassword']
    email = request.form['email']

    if username in users:
        flash('用戶名已經存在')
        return redirect(url_for('index'))

    hashed_password = generate_password_hash(password)
    users[username] = {'password': hashed_password, 'email': email}
    flash('註冊成功！')
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    if username not in users or not check_password_hash(users[username]['password'], password):
        flash('用戶名或密碼錯誤')
        return redirect(url_for('index'))

    session['username'] = username
    flash('登入成功！')
    return redirect(url_for('profile'))

@app.route('/profile')
def profile():
    if 'username' not in session:
        flash('請先登入')
        return redirect(url_for('index'))

    username = session['username']
    return f"歡迎, {username}! <a href='/logout'>登出</a>"

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('您已登出')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)