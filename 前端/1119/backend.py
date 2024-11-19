import os ##
from flask import Flask, request, render_template,jsonify, redirect, url_for, session, flash, send_from_directory
from werkzeug.utils import secure_filename
from flask_cors import CORS
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import jsonify
from utils import simplify_review
import hashlib
import secrets
from flask import request, jsonify
import time
import random
import urllib.parse
import requests   #機
import json  #機
import re  

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 用於會話管理，請替換為你的秘密金鑰

# 設定圖片存放路徑
UPLOAD_FOLDER = r'C:\Users\ntubimd\Desktop\BeautyBuddy\首頁\uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# 確保上傳的檔案類型安全
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def analyze_face(image_path):
    api_url = "https://api-us.faceplusplus.com/facepp/v3/detect"
    api_key = "7IFBZr-GQI37nGOhlYAAvt7FSgMyslqt"  # 替換為您從 Face++ 獲取的 API Key
    api_secret = "T-KUkQPZIiGzRB434vy-EirvZDMmhePY"  # 替換為您的 API Secret

    with open(image_path, 'rb') as image_file:
        response = requests.post(api_url, data={
            'api_key': api_key,
            'api_secret': api_secret,
            'return_attributes': 'age,gender,skinstatus'
        }, files={'image_file': image_file})

    if response.status_code == 200:
        result = response.json()
        if 'faces' in result and len(result['faces']) > 0:
            return result  # 返回完整的 API 結果
        else:
            return None  # 未檢測到人臉
    else:
        raise Exception(f"API Error: {response.status_code} - {response.text}")

class Database:
    def __init__(self, host, port, dbname, username, pwd):
        self.host = host
        self.port = port
        self.database = dbname
        self.user = username
        self.password = pwd
        self.__server = None

    def setServer(self):
        """建立資料庫連線，如果尚未連接或連接已失效"""
        if self.__server is None or not self.__server.is_connected():
            self.__server = mysql.connector.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )

    def getSqlData(self, sql, data=None):
        """執行查詢並返回結果集"""
        self.setServer()
        cursor = self.__server.cursor()
        try:
            cursor.execute(sql, data)
            return cursor.fetchall()  # 返回查詢結果
        finally:
            cursor.close()
            self.close()  # 確保關閉連接

    def executeSql(self, sql, data=None):
        """執行插入、更新或刪除語句"""
        self.setServer()
        cursor = self.__server.cursor()
        try:
            cursor.execute(sql, data)
            self.__server.commit()
        finally:
            cursor.close()

    def close(self):
        """關閉資料庫連線"""
        if self.__server and self.__server.is_connected():
            self.__server.close()

# 資料庫連線配置
db_config = {
    'host': "140.131.114.242",
    'port': 3306,
    'dbname': "113-113412",
    'username': "Beauty",
    'pwd': "6Eauty@110460"
}

# 定義一個裝飾器來保護需要登入的路由
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('請先登入。', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

######
# 檢查文件是否為允許的檔案類型
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=["GET"])
def home():
    username = session.get('username')  # 从session中获取用户名
    
    db = Database(**db_config)
    try:
        # 查詢每個類別的最高分產品
        categories = ['%防曬%', '%粉底液%', '%粉餅%']  # 可以根据需要添加其他类别
        highest_rated_products = {}

        # 查詢所有符合 p_{數字} 的資料表
        cursor = db.getSqlData("SHOW TABLES")
        table_names = [table[0] for table in cursor if table[0].startswith('p_')]  # 獲取所有 p_{數字} 的表名


        for category in categories:
            for table_name in table_names:
            # 修改查询以包括 ImageURL
                sql = f"""
                    SELECT pa.product_name, pa.product_id, pa.brand_name, pa.avg_rating, p.ImageURL
                    FROM ProductAverageRatings pa
                    JOIN {table_name} p ON pa.product_name = p.Name  # 使用动态表名
                    WHERE pa.category LIKE %s
                    ORDER BY pa.avg_rating DESC
                    LIMIT 1
                """
                data = (category,)
                result = db.getSqlData(sql, data)

                if result:
                    highest_rated_products[category] = {
                        'product_name': result[0][0],
                        'product_id': result[0][1],
                        'brand_name': result[0][2],
                        'avg_rating': result[0][3],
                        'img': result[0][4]  # 添加 ImageURL
                    }

             # 查詢 ImageUrls 表的最新分析結果
        sql_image_urls = """
            SELECT image_url, upload_time, analysis_result 
            FROM ImageUrls 
            WHERE user_id = %s 
            ORDER BY upload_time DESC 
            LIMIT 1
        """
        user_id = session.get('user_id')
        data_image_urls = (user_id,)
        latest_analysis_result = db.getSqlData(sql_image_urls, data_image_urls)

        # 處理 analysis_result
        latest_result = None
        if latest_analysis_result:
            analysis_result_str = latest_analysis_result[0][2]
            if analysis_result_str:
                try:
                    match = re.search(r"膚質: ({.*?}), 年齡: (\d+)", analysis_result_str)
                    if match:
                        skin_data_str = match.group(1).replace("'", '"')
                        skin_data = json.loads(skin_data_str)
                        latest_result = {
                            'health': skin_data.get('health', 'N/A'),
                            'stain': skin_data.get('stain', 'N/A'),
                            'dark_circle': skin_data.get('dark_circle', 'N/A'),
                            'acne': skin_data.get('acne', 'N/A'),
                            'age': match.group(2)
                        }
                except Exception as e:
                    print(f"解析失敗: {e}")

    except mysql.connector.Error as err:
        flash(f"資料庫錯誤: {str(err)}", 'danger')
    finally:
        db.close()

    return render_template('home.html', username=username, highest_rated_products=highest_rated_products)


#####抓ID
@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': '沒有選擇文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '沒有選擇文件'}), 400

    # 確保上傳的檔案是圖片
    if file and allowed_file(file.filename):
        # 生成唯一的檔案名稱，避免覆蓋
        timestamp = int(time.time())  # 使用時間戳記生成唯一名稱
        filename = f"{timestamp}_{secure_filename(file.filename)}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # 儲存圖片到指定資料夾
        file.save(filepath)

        # 回傳包含完整網域的圖片 URL
        image_url = f"http://beautybuddy.ddns.net/uploads/{filename}"

        # 檢查使用者是否登入，並取得使用者名稱
        username = session.get('user_id', None)  # 這裡假設 'user_id' 儲存的是 Username
        user_id = username if username else None

        # 取得上傳時間
        upload_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

        # 預設分析結果
        analysis_result = ""

        # 呼叫人臉分析 API
        try:
            analysis_result = analyze_face(filepath)  # 使用機器學習或 API 進行分析
            if analysis_result:
                analysis_result = f"膚質: {analysis_result['faces'][0]['attributes']['skinstatus']}, 年齡: {analysis_result['faces'][0]['attributes']['age']['value']}"
            else:
                analysis_result = "無法檢測到人臉"
        except Exception as e:
            analysis_result = f"分析失敗: {str(e)}"

        # 建立資料庫連接
        db = Database(db_config['host'], db_config['port'], db_config['dbname'], db_config['username'], db_config['pwd'])

        # 插入圖片資料到 ImageUrls 表
        sql = """
        INSERT INTO ImageUrls (image_url, user_id, upload_time, analysis_result)
        VALUES (%s, %s, %s, %s)
        """

        # 執行插入語句
        db.executeSql(sql, (image_url, user_id, upload_time, analysis_result))

        return jsonify({'image_url': image_url, 'analysis_result': analysis_result})

    return jsonify({'error': '檔案格式不正確'}), 400

# 用來展示上傳的圖片
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/detect_recommend', methods=['POST'])
def detect_recommend():
    analysis_data = request.json
    health = analysis_data.get('health', '')
    stain = analysis_data.get('stain', '')
    dark_circle = analysis_data.get('dark_circle', '')
    acne = analysis_data.get('acne', '')

    # 檢查是否有 '無法檢測到人臉' 的結果
    if health == '無法檢測到人臉' or stain == '無法檢測到人臉' or dark_circle == '無法檢測到人臉' or acne == '無法檢測到人臉':
        return jsonify({'error': '該筆偵測無法檢測到人臉，請再上傳正面照來查看推薦產品！'})

    try:
        # 如果可以轉換為數字，則進行轉換
        health = float(health)
        stain = float(stain)
        dark_circle = float(dark_circle)
        acne = float(acne)
    except ValueError:
        # 如果無法轉換（可能是 '無法檢測到人臉'），則返回錯誤
        return jsonify({'error': '偵測數值無效，請上傳有效的照片進行測試！'})

    # 你的後續邏輯保持不變
    # 這裡的程式碼將根據傳入的 health, stain, dark_circle, acne 來進行產品推薦的邏輯
    conditions = [
        {"label": "健康度", "key": "health", "value": health, "limit": 50, "recommend": health <= 50,
         "keywords": ['柔膚', '中性肌', '全能', '調理', '極潤', '緊緻', '輕透', '全效', '肌淨', '維他命']},
        {"label": "斑點值", "key": "stain", "value": stain, "limit": 50, "recommend": stain >= 50,
         "keywords": ['無暇', '淨白', '美白', '亮白', '光澤', '撫平', '亮采', '瞬白', '透白', '潤色', '提亮']},
        {"label": "黑眼圈值", "key": "dark_circle", "value": dark_circle, "limit": 50, "recommend": dark_circle >= 50,
         "keywords": ['無暇', '淨白', '美白', '亮白', '柔霧', '亮采', '較色', '瞬白', '透白', '潤色']},
        {"label": "痘痘值", "key": "acne", "value": acne, "limit": 40, "recommend": acne >= 40,
         "keywords": ['控油', '保濕', '痘痘肌', '抗痘', '敏感肌', '透白', '維他命', '輕透', '零妝感']}
    ]

    recommended_products = []
    db = Database(**db_config)

    try:
        # 獲取所有產品表
        tables = db.getSqlData("SHOW TABLES")
        product_tables = [t[0] for t in tables if t[0].startswith('p_')]

        for condition in conditions:
            label = condition["label"]
            keywords = condition["keywords"]

            if not condition["recommend"]:
                recommended_products.append({"label": label, "products": [], "message": "目前不需要此類產品！"})
                continue

            all_products = []
            for table in product_tables:
                sql = f"""
                    SELECT Name, Brand, Category, `Size and Price`, ImageURL, Rating
                    FROM {table}
                    WHERE Category IN ('隔離霜', '眼部打底', '其它妝前', '遮瑕膏', '遮瑕筆', '眼部遮瑕', '其它遮瑕',
                                       '粉底液', '粉餅', '粉霜', '氣墊粉餅', 'BB霜', 'CC霜', '其它粉底', '蜜粉', '蜜粉餅')
                      AND ({' OR '.join([f"Name LIKE '%{kw}%'" for kw in keywords])})
                    ORDER BY Rating DESC
                    LIMIT 4
                """
                all_products += db.getSqlData(sql)

            # 若有符合條件的產品
            recommended_products.append({
                "label": label,
                "products": [
                    {
                        "name": p[0],
                        "brand": p[1],
                        "category": p[2],
                        "size_and_price": p[3],
                        "image_url": p[4],
                        "rating": p[5]
                    }
                    for p in all_products
                ],
                "message": None if all_products else "目前無符合條件的推薦產品！"
            })

        return jsonify(recommended_products)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()



#//////////
@app.route('/get_recommendations', methods=['POST'])      # 表單的
def get_recommendations():
    # 假設前端會發送一個 JSON 包含 'result' 字段，例如 {'result': '敏感乾性肌膚'}
    data = request.json
    result = data.get('result', '')

    keywords = []
    if '乾性' in result:
        keywords.append('%乾性%')
    if '油性' in result:
        keywords.append('%油性%')
    if '混合' in result:
        keywords.append('%混合%')

    if not keywords:
        return jsonify({'error': '未匹配到任何膚質類型關鍵字'})

    db = Database(**db_config)
    recommendations = []
    seen_products = set()  # 使用集合來跟蹤已添加的產品
    try:
         # 查詢所有符合 p_{數字} 的資料表
        cursor = db.getSqlData("SHOW TABLES")
        product_tables = [table[0] for table in cursor if table[0].startswith('p_')]  # 獲取所有 p_{數字} 的表名

        # 逐個關鍵字查詢，並篩選 SkinTypeRating 最高的三個產品
        for keyword in keywords:
                for product_table in product_tables:
                    sql = f"""
                        SELECT r.brand_name, r.product_name, r.size, r.price, p.ImageURL
                        FROM Reviews  r
                        JOIN {product_table} p ON r.product_name = p.Name  -- 使用名稱進行關聯  ##Products
                        WHERE r.BestSkinType LIKE %s
                        ORDER BY r.SkinTypeRating DESC
                        LIMIT 3
                    """
                    data = (keyword,)
                    results = db.getSqlData(sql, data)
                    
                    for row in results:
                        product_key = (row[0], row[1], row[2])  # 使用品牌、產品名稱和尺寸作為唯一標識
                        if product_key not in seen_products:  # 如果未添加過，則添加到推薦列表
                            seen_products.add(product_key)
                            recommendations.append({
                                'brand_name': row[0], 
                                'product_name': row[1], 
                                'size': row[2], 
                                'price': row[3],
                                'image_url': row[4]  # 新增這一行以獲取 ImageURL
                            })

    except mysql.connector.Error as err:
        return jsonify({'error': str(err)})
    finally:
        db.close()

    # 返回正確的 JSON 數據
    return jsonify({'recommendations': recommendations})

@app.route('/skin_tests_page', methods=['GET'])
@login_required
def skin_tests_page():
    username = session.get('username')
    db = Database(**db_config)

    try:
        sql = "SELECT Sensitivity, Hydration, Oiliness, Result, TestDate FROM SkinTests WHERE Username = %s"
        data = (username,)
        results = db.getSqlData(sql, data)

        skin_tests = [{
            'sensitivity': row[0],
            'hydration': row[1],
            'oiliness': row[2],
            'result': row[3],
            'test_date': row[4]
        } for row in results]

        return render_template('skin_tests.html', skin_tests=skin_tests)
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        db.close()

@app.route('/submit_skin_test', methods=['POST'])
@login_required
def submit_skin_test():
    data = request.get_json()
    sensitivity = data.get('sensitivity')
    hydration = data.get('hydration')
    oiliness = data.get('oiliness')
    result = data.get('result')

    if not all([sensitivity, hydration, oiliness, result]):
        return jsonify({'success': False, 'message': '缺少必要的數據'}), 400

    username = session.get('username')

    db = Database(**db_config)
    try:
        sql = """
            INSERT INTO SkinTests (Username, Sensitivity, Hydration, Oiliness, Result)
            VALUES (%s, %s, %s, %s, %s)
        """
        data = (username, sensitivity, hydration, oiliness, result)
        db.executeSql(sql, data)
        return jsonify({'success': True}), 200
    except mysql.connector.Error as err:
        return jsonify({'success': False, 'message': str(err)}), 500
    finally:
        db.close()

@app.route('/filter', methods=["GET"])
def filter():
    username = session.get('username')  # 从 session 中获取用户名

    # 初始化數據庫連接
    db = Database(**db_config)

    # 獲取所有 p_{數字} 表的名稱
    tables_query = "SHOW TABLES"
    all_tables = [row[0] for row in db.getSqlData(tables_query)]
    product_tables = [table for table in all_tables if table.startswith('p_')]

    # 從所有 p_{數字} 表中提取品牌名稱
    brands = set()  # 使用集合避免重複
    for table in product_tables:
        query = f"SELECT DISTINCT Brand FROM {table}"
        results = db.getSqlData(query)
        brands.update(row[0] for row in results if row[0])  # 避免空值

    db.close()

    # 將品牌轉換為列表並排序
    brands = sorted(brands)

    # 渲染模板並傳遞品牌列表
    return render_template('filter.html', username=username, brands=brands)

@app.route('/match', methods=['GET'])
def match():
    db = Database(**db_config)
    price_range = request.args.get('price', '全部範圍')
    brand_preference = request.args.get('brand', '全部品牌')
    category_preference = request.args.get('category', '全部類別')

    # 獲取所有符合條件的 p_{數字} 表
    cursor = db.getSqlData("SHOW TABLES")
    product_tables = [table[0] for table in cursor if table[0].startswith('p_')]

    # 初始化查詢條件
    filters = []

    # 價格範圍篩選
    price_condition = ""
    if price_range == '1~250元':
        price_condition = "AND (r.price BETWEEN 1 AND 250 OR r.price IS NULL)"
    elif price_range == '251~400元':
        price_condition = "AND (r.price BETWEEN 251 AND 400 OR r.price IS NULL)"
    elif price_range == '401元以上':
        price_condition = "AND (r.price > 400 OR r.price IS NULL)"

    # 品牌偏好篩選
    brand_condition = ""
    if brand_preference and brand_preference != '全部品牌':
        brand_condition = "AND r.brand_name = %s"
        filters.append(brand_preference)

    # 產品類別篩選
    category_condition = ""
    if category_preference and category_preference != '全部類別':
        if category_preference == '防曬':
            category_condition = "AND (r.category LIKE '%防曬%' OR r.category IS NULL)"
        else:
            category_condition = "AND r.category = %s"
            filters.append(category_preference)

    # 查詢最新的檢測結果
    latest_test_query = """
        SELECT Result
        FROM SkinTests
        WHERE Username = %s
        ORDER BY TestDate DESC
        LIMIT 1
    """

    try:
        # 獲取最新的測驗結果
        username = session.get('username')
        latest_result = None  # 初始化為 None

        if username:
            result = db.getSqlData(latest_test_query, (username,))
            if result:
                latest_result = result[0][0]  # 取得最新測驗結果
            else:
                latest_result = "你還沒測驗膚質喔！趕快去測來看您與產品的匹配度吧～"  # 沒有測試結果的情況

        # 根據測驗結果的關鍵字篩選 BestSkinType 欄位
        skin_type_condition = ""
        if latest_result and latest_result != "你還沒測驗膚質喔！趕快去測來看您與產品的匹配度吧～":
            if '乾性' in latest_result:
                skin_type_condition = "AND r.BestSkinType LIKE '%乾性%'"
            elif '油性' in latest_result:
                skin_type_condition = "AND r.BestSkinType LIKE '%油性%'"
            elif '混合' in latest_result:
                skin_type_condition = "AND r.BestSkinType LIKE '%混合%'"

        # 構建查詢，遍歷所有 product_tables
        # 構建查詢，遍歷所有 product_tables
        # 構建查詢，遍歷所有 product_tables
        products = []
        for product_table in product_tables:
            query = f"""
                SELECT r.brand_name, r.product_name, r.size, r.price, r.category, p.ImageURL, 
                    COALESCE(r.SkinTypeRating, '未獲取') AS SkinTypeRating
                FROM Reviews r
                JOIN {product_table} p ON r.product_name = p.Name
                WHERE 1=1
                {price_condition}
                {brand_condition}
                {category_condition}
                {skin_type_condition}
                GROUP BY r.brand_name, r.product_name, r.size, r.price, r.category, p.ImageURL, r.SkinTypeRating
                ORDER BY r.SkinTypeRating DESC
            """

            # 執行查詢並追加結果
            results = db.getSqlData(query, tuple(filters))
            products.extend(results)


        # 返回匹配的產品
        return render_template('match.html', products=products, user_result=latest_result, username=username)

    except mysql.connector.Error as err:
        return f"Error: {str(err)}", 500
    finally:
        db.close()

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.json.get('email')  # 改用 request.json
        password = request.json.get('password')

        db = Database(**db_config)
        try:
            sql = "SELECT UserID, Username, Email, Password FROM Users WHERE Email = %s"
            data = (email,)
            results = db.getSqlData(sql, data)

            if results:
                user = results[0]
                user_id, username, user_email, user_password = user

                if check_password_hash(user_password, password):
                    session['user_id'] = user_id
                    session['username'] = username
                    return jsonify({"success": True, "message": "登入成功！"})
                else:
                    return jsonify({"success": False, "message": "密碼錯誤。"}), 401
            else:
                return jsonify({"success": False, "message": "找不到該電子郵件對應的帳號。"}), 404
        except mysql.connector.Error as err:
            return jsonify({"success": False, "message": f"資料庫錯誤: {str(err)}"}), 500
        finally:
            db.close()

    return render_template('login.html')  # GET請求時，返回HTML

@app.route('/register', methods=["GET", "POST"])
def register(): 
    if request.method == "POST":
        username = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirmPassword')  # 確認密碼

        # 檢查兩次輸入的密碼是否一致
        if password != confirm_password:
            flash('密碼與確認密碼不匹配。', 'danger')
            return render_template('register.html')  # 密碼不匹配时，返回主頁

        # 使用 werkzeug.security 模組的 generate_password_hash 函數來加密密碼
        # 這裡生成的密碼哈希會存儲到資料庫，而不是存儲原始密碼

#PBKDF2 演算法
        hashed_password = generate_password_hash(password)  # 註冊加密 

        db = Database(**db_config)
        try:
              # 將新用戶的名稱、電子郵件和加密後的密碼插入到資料庫
            sql = "INSERT INTO Users (Username, Email, Password) VALUES (%s, %s, %s)"
            data = (username, email, hashed_password)  # 使用加密後的密碼
            db.executeSql(sql, data)  # 插入用户數據
            flash('註冊成功！請登入。', 'success')  # 添加成功提示
            return redirect(url_for('login'))  # 重定向到登錄頁面

        # 如果資料庫中已有相同的電子郵件或名稱，則處理重複鍵錯誤
        except mysql.connector.IntegrityError as ie:
            print(f"IntegrityError: {ie}")  # 調試信息，輸出錯誤信息
            if ie.errno == 1062:  # 重複鍵錯誤碼
                flash('電子郵件或用戶名已被註冊。', 'danger')  # 提示使用者已註冊
            else:
                flash(f"資料庫錯誤: {str(ie)}", 'danger')
        except mysql.connector.Error as err:
            flash(f"資料庫錯誤: {str(err)}", 'danger')
        finally:
            db.close()

    return render_template('register.html')  # GET請求時，渲染註冊頁面

@app.route('/logout')
def logout():
    session.clear()
    flash('已成功登出。', 'success')
    return redirect(url_for('home'))

@app.route('/forgot_password', methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get('email')  # 獲取用戶輸入的電子郵件
        db = Database("140.131.114.242", 3306, "113-113412", "Beauty", "6Eauty@110460")
        db.setServer()
        cursor = db.Server.cursor(dictionary=True)

        # 檢查電子郵件是否存在於資料庫中
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user:
            token = secrets.token_urlsafe(16)
            reset_link = url_for('forgot_or_reset_password', token=token, _external=True)
            # 在此處發送重設密碼的電子郵件，這部分省略
            flash(f'重設密碼的連結已發送至 {email}。', 'info')
            cursor.execute("UPDATE users SET reset_token = %s WHERE email = %s", (token, email))
            db.Server.commit()
        else:
            flash('該電子郵件未註冊。', 'error')

    username = session.get('username')  # 從 session 中獲取用戶名
    return render_template('forgot_password.html', username=username)

@app.route('/profile', methods=['GET'])
def profile():
    user_id = session.get('user_id')
    if not user_id:
        flash('請先登入。', 'warning')
        return redirect(url_for('login'))

    db = Database(**db_config)

    try:
        # 擴展 SQL 查詢以包含 Password 和 CreatedAt
        sql_user = "SELECT Username, Email, Password, CreatedAt FROM Users WHERE UserID = %s"
        data_user = (user_id,)
        user_results = db.getSqlData(sql_user, data_user)

        if user_results:
            user = user_results[0]
            username = user[0]
            email = user[1]
            password = user[2]
            created_at = user[3]

            # 獲取皮膚檢測、評論、收藏等資訊（保持不變）
            sql_tests = "SELECT Sensitivity, Hydration, Oiliness, Result, TestDate FROM SkinTests WHERE Username = %s ORDER BY TestDate DESC"
            data_tests = (username,)
            skin_tests = db.getSqlData(sql_tests, data_tests)

            sql_reviews = """
                SELECT brand_name, product_name, size, price, category, rating, usage_info, experience_method, usage_season, usage_environment, review_content, CreatedDate, SimplifiedReview
                FROM Reviews
                WHERE Username = %s
                ORDER BY CreatedDate DESC
            """
            data_reviews = (username,)
            reviews = db.getSqlData(sql_reviews, data_reviews)

            # 查詢 ImageUrls 表，篩選目前登入用戶的資料
            sql_image_urls = """
                SELECT image_url, upload_time, analysis_result 
                FROM ImageUrls 
                WHERE user_id = %s 
                ORDER BY upload_time DESC
            """
            data_image_urls = (user_id,)
            image_urls_results = db.getSqlData(sql_image_urls, data_image_urls)

               # === 添加處理 analysis_result 的代碼 ===
            processed_results = []
            for image_url_result in image_urls_results:
                image_url = image_url_result[0]
                upload_time = image_url_result[1]
                analysis_result_str = image_url_result[2]  # 假設 analysis_result 是這種格式的字符串

                if analysis_result_str:
                    try:
                        # 使用正則表達式提取膚質數值
                        skin_data_match = re.search(r"膚質: ({.*?}), 年齡: (\d+)", analysis_result_str)
                        if skin_data_match:
                            skin_data_str = skin_data_match.group(1)  # 提取膚質部分
                            age = skin_data_match.group(2)  # 提取年齡部分
                            
                            # 將單引號替換為雙引號，轉換為 JSON 格式
                            skin_data_str = skin_data_str.replace("'", '"')
                            skin_data = json.loads(skin_data_str)  # 轉換為 Python 字典
                            
                            health = skin_data.get('health', 'N/A')
                            stain = skin_data.get('stain', 'N/A')
                            dark_circle = skin_data.get('dark_circle', 'N/A')
                            acne = skin_data.get('acne', 'N/A')
                        else:
                            health = stain = dark_circle = acne = "無法檢測到人臉"
                    except Exception as e:
                        # 如果有任何解析錯誤
                        print(f"解析失敗: {e} - 原始值: {analysis_result_str}")
                        health = stain = dark_circle = acne = "解析失敗"
                else:
                    # 如果分析結果為空
                    health = stain = dark_circle = acne = "無數據"

                # 將處理後的結果追加到列表
                processed_results.append((image_url, upload_time, health, stain, dark_circle, acne))



            # 獲取所有 p_{數字} 表
            cursor = db.getSqlData("SHOW TABLES")
            product_tables = [table[0] for table in cursor if table[0].startswith('p_')]

            # 變更收藏查詢，動態查詢多個 p_{數字} 表
            favorites = []

           # 逐個查詢所有 p_{數字} 表
            for product_table in product_tables:
                sql_favorites = f"""
                    SELECT f.product_name, f.brand, f.category, f.sizeprice, f.created_at, p.ImageURL
                    FROM Favorites AS f
                    JOIN {product_table} AS p ON f.product_name = p.Name
                    WHERE f.Username = %s
                """
                data_favorites = (username,)
                favorites_results = db.getSqlData(sql_favorites, data_favorites)
                
                # 將查詢結果加入 favorites
                for row in favorites_results:
                    favorites.append({
                        'product_name': row[0],
                        'brand': row[1],
                        'category': row[2],
                        'sizeprice': row[3],
                        'created_at': row[4],
                        'image_url': row[5]
                    })
            

            # 獲取 section 參數，預設為 'skin-tests'
            section = request.args.get('section', 'skin-tests')

            # 傳遞 password 和 created_at 到模板
            return render_template('profile.html', username=username, email=email, password=password, created_at=created_at, skin_tests=skin_tests, reviews=reviews, favorites=favorites, section=section,image_urls_results=processed_results)
        else:
            flash('找不到用戶資料。', 'danger')
            return redirect(url_for('home'))
    except mysql.connector.Error as err:
        flash(f"資料庫錯誤: {str(err)}", 'danger')
        return redirect(url_for('sun'))
    finally:
        db.close()

@app.route('/add_favorite', methods=["POST"])
def add_favorite():
    try:
        username = session.get('username')  # 從 session 中獲取使用者名稱

        # 檢查是否登入
        if not username:
            return jsonify({'status': 'error', 'message': '請登入即可收藏'}), 401


        data = request.json
        product_name = data.get('product_name')
        brand = data.get('brand')
        category = data.get('category')
        sizeprice = data.get('sizeprice')
        img_url = data.get('img_url')

        if not all([product_name, brand, category, sizeprice, img_url]):
            return jsonify({'status': 'error', 'message': 'Missing data'}), 400

        db = Database(**db_config)

        # 檢查是否已經存在該產品
        check_sql = "SELECT COUNT(*) FROM Favorites WHERE product_name = %s AND username = %s"
        existing = db.getSqlData(check_sql, (product_name, username))
        if existing and existing[0][0] > 0:
            return jsonify({'status': 'error', 'message': '此商品已經收藏囉'}), 409

        sql = """
        INSERT INTO Favorites (username, product_name, brand, category, sizeprice, img_url)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (username, product_name, brand, category, sizeprice, img_url)
        db.executeSql(sql, values)
        return jsonify({'status': 'success'}), 200

    except mysql.connector.Error as err:
        print(f"Database error: {str(err)}")
        return jsonify({'status': 'error', 'message': str(err)}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Internal Server Error'}), 500
    finally:
        db.close()

@app.route('/add_comment', methods=['POST'])
def add_comment():
    user_id = session.get('user_id')
    if not user_id:
        flash('請先登入。', 'warning')
        return redirect(url_for('login'))

    # 獲取表單數據
    brand_name = request.form['brand_name']
    product_name = request.form['product_name']
    size = request.form['size']
    price = request.form['price']
    category = request.form['category']
    rating = request.form['rating']
    usage_info = request.form['usage_info']
    experience_method = request.form['experience_method']
    usage_season = request.form['usage_season']
    usage_environment = request.form['usage_environment']
    review_content = request.form['review_content']

    db = Database(**db_config)

    try:
        sql_insert = """
        INSERT INTO Contents (brand_name, product_id, product_name, size, price, category, rating, usage_info, effect, experience_method, usage_season, usage_environment, review_content, Username)
        VALUES (%s, NULL, %s, %s, %s, %s, %s, %s, NULL, %s, %s, %s, %s, %s)
        """
        data_insert = (brand_name, product_name, size, price, category, rating, usage_info, experience_method, usage_season, usage_environment, review_content, session.get('username'))
        
        db.executeSql(sql_insert, data_insert)
        flash('評論已成功提交！', 'success')
    except mysql.connector.Error as err:
        flash(f"資料庫錯誤: {str(err)}", 'danger')
    finally:
        db.close()

    return redirect(url_for('profile', section='add-comment'))

@app.route('/sun', methods=["GET"])
def sun():
    db = Database(**db_config)
    try:
        # 查詢所有 p_{數字} 表
        cursor = db.getSqlData("SHOW TABLES")
        product_tables = [table[0] for table in cursor if table[0].startswith('p_')]  # 獲取所有 p_{數字} 的表名
        
        # 存放所有查詢結果的列表
        products = []

        # 遍歷所有 p_{數字} 表進行查詢
        for product_table in product_tables:
            # 動態生成查詢語句，替換 JOIN 表名
            sql = f"""
                SELECT * FROM {product_table} 
                WHERE category LIKE %s
            """
            data = ("%防曬%",)  
            results = db.getSqlData(sql, data)
            
            for row in results:
                product = {
                    'id': row[0],
                    'brand': row[1],
                    'name': row[2],
                    'category': row[3],
                    'sizeprice': row[4],
                    'des': row[5],
                    'img': row[6],
                }
                
                # 查詢 NewReviewSummary 表中的 avg_rating
                rating_sql = "SELECT avg_rating FROM NewReviewSummary WHERE product_name = %s"
                rating_data = (row[2],)  # row[2] 是 product_name
                rating_result = db.getSqlData(rating_sql, rating_data)
                product['avg_rating'] = rating_result[0][0] if rating_result else None

                products.append(product)
        
        return render_template('sun.html', products=products, username=session.get('username'))
    except mysql.connector.Error as err:
        return f"Error: {str(err)}", 500
    finally:
        db.close()

@app.route('/liquid', methods=["GET"])
def liquid():
    db = Database(**db_config)
    try:
        # 查詢所有 p_{數字} 表
        cursor = db.getSqlData("SHOW TABLES")
        product_tables = [table[0] for table in cursor if table[0].startswith('p_')]  # 獲取所有 p_{數字} 的表名
        
        products = []

        # 遍歷所有 p_{數字} 表進行查詢
        for product_table in product_tables:
            # 動態生成查詢語句，替換 JOIN 表名
            sql = f"""
                SELECT * FROM {product_table}
                WHERE category LIKE %s
            """
            data = ("%粉底液%",)  
            results = db.getSqlData(sql, data)

            for row in results:
                product = {
                    'id': row[0],
                    'brand': row[1],
                    'name': row[2],
                    'category': row[3],
                    'sizeprice': row[4],
                    'des': row[5],
                    'img': row[6],
                }
                
                # 查詢 NewReviewSummary 表中的 avg_rating
                rating_sql = "SELECT avg_rating FROM NewReviewSummary WHERE product_name = %s"
                rating_data = (row[2],)  # row[2] 是 product_name
                rating_result = db.getSqlData(rating_sql, rating_data)
                product['avg_rating'] = rating_result[0][0] if rating_result else None

                products.append(product)

        return render_template('liquid.html', products=products, username=session.get('username'))
    except mysql.connector.Error as err:
        return f"Error: {str(err)}", 500
    finally:
        db.close()

@app.route('/cookie', methods=["GET"])
def cookie():
    db = Database(**db_config)
    try:
        # 查詢所有 p_{數字} 表
        cursor = db.getSqlData("SHOW TABLES")
        product_tables = [table[0] for table in cursor if table[0].startswith('p_')]  # 獲取所有 p_{數字} 的表名
        
        products = []

        # 遍歷所有 p_{數字} 表進行查詢
        for product_table in product_tables:
            # 動態生成查詢語句，替換 JOIN 表名
            sql = f"""
                SELECT * FROM {product_table}
                WHERE category LIKE %s
            """
            data = ("%粉餅%",)  
            results = db.getSqlData(sql, data)

            for row in results:
                product = {
                    'id': row[0],
                    'brand': row[1],
                    'name': row[2],
                    'category': row[3],
                    'sizeprice': row[4],
                    'des': row[5],
                    'img': row[6],
                }
                
                # 查詢 NewReviewSummary 表中的 avg_rating
                rating_sql = "SELECT avg_rating FROM NewReviewSummary WHERE product_name = %s"
                rating_data = (row[2],)  # row[2] 是 product_name
                rating_result = db.getSqlData(rating_sql, rating_data)
                product['avg_rating'] = rating_result[0][0] if rating_result else None

                products.append(product)

        return render_template('cookie.html', products=products, username=session.get('username'))
    except mysql.connector.Error as err:
        return f"Error: {str(err)}", 500
    finally:
        db.close()

@app.route('/products', methods=['GET'])  # 搜尋欄
def get_products():
    keyword = request.args.get('keyword')
    print(f"Keyword received: {keyword}")  # 測試用
    db = Database(**db_config)
    
    try:
        # 查詢所有 p_{數字} 表
        cursor = db.getSqlData("SHOW TABLES")
        product_tables = [table[0] for table in cursor if table[0].startswith('p_')]  # 獲取所有 p_{數字} 的表名
        
        products = []
        
        # 遍歷所有 p_{數字} 表進行查詢
        for product_table in product_tables:
            # 使用 f"" 動態生成查詢語句
            sql = f"""
                SELECT * FROM {product_table}
                WHERE name LIKE %s
            """
            data = (f"%{keyword}%",)
            results = db.getSqlData(sql, data)
            
            # 將查詢結果添加到 products 列表中
            for row in results:
                product = {
                    'id': row[0],             # ProductID
                    'brand': row[1],          # Brand
                    'name': row[2],           # Name
                    'sizeprice': row[3],      # Size and Price
                    'category': row[4],       # Category
                    'rating': row[5],         # Rating
                    'img': row[6],            # ImageURL
                    'des': row[7].split('・'),  # Description (分割成多行)
                }
                products.append(product)
        
        return render_template('search.html', products=products, keyword=keyword, username=session.get('username'))  # 傳遞關鍵字到模板
    except mysql.connector.Error as err:
        return f"Error: {str(err)}", 500
    finally:
        db.close()

@app.route('/product_detail/<path:product_name>', methods=["GET"])
def product_detail(product_name):
    # 解碼 URL 參數
    product_name = urllib.parse.unquote(product_name)
    db = Database(**db_config)
    try:
        # 查詢所有 p_{數字} 表
        cursor = db.getSqlData("SHOW TABLES")
        product_tables = [table[0] for table in cursor if table[0].startswith('p_')]  # 獲取所有 p_{數字} 的表名

        product = None

        # 遍歷所有 p_{數字} 表，查詢目標產品
        for product_table in product_tables:
            # 使用 f"" 動態生成查詢語句，查詢 p_{數字} 表
            sql = f"SELECT * FROM {product_table} WHERE name = %s"
            data = (product_name,)
            result = db.getSqlData(sql, data)

            if result:
                product = {
                    'id': result[0][0],
                    'brand': result[0][1],
                    'name': result[0][2],
                    'sizeprice': result[0][3],  # 調整索引以匹配 get_products 的變更
                    'category': result[0][4],
                    'des': result[0][7],
                    'img': result[0][6],
                }
                break  # 找到產品後就停止查詢其他表

        if not product:
            flash('找不到產品資料。', 'danger')
            return redirect(url_for('home'))

        # 查詢該產品的評分，處理 None 值
        rating_sql = "SELECT avg_rating FROM NewReviewSummary WHERE product_name = %s"
        rating_data = (product_name,)
        rating_result = db.getSqlData(rating_sql, rating_data)
        avg_rating = rating_result[0][0] if rating_result and rating_result[0][0] is not None else 0  # 如果是 None，設為 0

        # 查詢該產品的評論
        review_sql = "SELECT SimplifiedReview, Keywords FROM Reviews WHERE product_name = %s"
        review_data = (product_name,)
        reviews_result = db.getSqlData(review_sql, review_data)

        reviews = [review[0] for review in reviews_result]  # 這裡的 review[0] 現在對應的是 `SimplifiedReview`
        keywords = reviews_result[0][1] if reviews_result else None

        product['rating'] = avg_rating  # 使用 avg_rating 作為產品的評分

        return render_template('des.html', product=product, reviews=reviews, keywords=keywords, username=session.get('username'))

    except mysql.connector.Error as err:
        flash(f"資料庫錯誤: {str(err)}", 'danger')
        return redirect(url_for('home'))
    finally:
        db.close()

@app.route('/simplify-review', methods=['POST'])
@login_required
def simplify_review_route():
    if request.method == 'POST':
        try:
            print("接收到簡化評論的請求")
            db = Database(
                host=db_config['host'],
                port=db_config['port'],
                dbname=db_config['dbname'],
                username=db_config['username'],
                pwd=db_config['pwd']
            )

            # 獲取尚未簡化的評論
            results = db.getSqlData("SELECT review_content FROM Contents WHERE SimplifiedReview IS NULL")
            print(f"獲取到 {len(results)} 條評論")

            simplified_reviews = []  # 儲存所有簡化的評論
            updates = []  # 準備批量更新

            for row in results:
                review_content = row[0]
                simplified_review, invalid_reason = simplify_review(review_content)

                if invalid_reason:
                    updates.append((invalid_reason, review_content))
                else:
                    simplified_reviews.append(simplified_review)
                    updates.append((simplified_review, review_content))

            # 批量更新評論
            for update in updates:
                db.executeSql("UPDATE Contents SET SimplifiedReview = %s WHERE review_content = %s", update)

            # 返回所有簡化的評論
            return jsonify({'message': '評論已成功簡化！', 'simplified_reviews': simplified_reviews})

        except Exception as e:
            print(f"錯誤發生: {e}")
            return jsonify({'message': f'錯誤發生: {e}'})



if __name__ == '__main__':
    # 確保 uploads 資料夾存在
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)

@app.route('/submit_discussion', methods=['POST'])
def submit_discussion():
    product_name = request.form.get('product_name')
    username = session.get('username', '匿名')  # 使用者名稱，如果未登入則為匿名
    comment = request.form.get('comment')

    if not comment:
        flash('留言內容不能為空')
        return redirect(request.referrer)

    # 將留言存入資料庫
    conn = mysql.connector.connect(
        host="140.131.114.242",
        port=3306,
        user="Beauty",
        password="6Eauty@110460",
        database="113-113412"
    )
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Discussions (product_name, username, comment) VALUES (%s, %s, %s)",
        (product_name, username, comment)
    )
    conn.commit()
    cursor.close()
    conn.close()

    flash('留言成功！')
    return redirect(request.referrer)

@app.route('/product_detail/<string:product_name>')
def product_detail(product_name):
    # 查詢產品資訊和留言
    conn = mysql.connector.connect(
        host="140.131.114.242",
        port=3306,
        user="Beauty",
        password="6Eauty@110460",
        database="113-113412"
    )
    cursor = conn.cursor(dictionary=True)

    # 查詢產品資訊
    cursor.execute("SELECT * FROM Products WHERE name = %s", (product_name,))
    product = cursor.fetchone()

    # 查詢留言
    cursor.execute("SELECT * FROM Discussions WHERE product_name = %s ORDER BY created_at DESC", (product_name,))
    discussions = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('product_detail.html', product=product, discussions=discussions)
