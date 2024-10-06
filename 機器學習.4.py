import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
import joblib
import mysql.connector

# 資料庫操作類
class Database:
    def __init__(self, host, port, dbname, username, pwd):
        self.host = host
        self.port = port
        self.database = dbname
        self.user = username
        self.password = pwd
        self.__server = None

    @property
    def Server(self):
        return self.__server

    @Server.setter
    def Server(self, value):
        self.__server = value

    def setServer(self):
        """建立資料庫連線，如果尚未連接或連接已失效"""
        if self.Server is None or not self.Server.is_connected():
            self.Server = mysql.connector.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )

    def test(self):
        """測試資料庫是否成功連接"""
        self.setServer()
        return self.Server.is_connected()

    def runSql(self, sql, data=None):
        """執行 SQL 插入、更新、刪除等語句"""
        self.setServer()
        cursor = self.Server.cursor()
        try:
            if data is None:
                cursor.execute(sql)
            else:
                cursor.execute(sql, data)
            self.Server.commit()  # 提交更改
        finally:
            cursor.close()

    def getSqlData(self, sql):
        """執行查詢並返回結果集"""
        self.setServer()
        cursor = self.Server.cursor()
        try:
            cursor.execute(sql)
            return cursor.fetchall()  # 返回查詢結果
        finally:
            cursor.close()

    def close(self):
        """關閉資料庫連線"""
        if self.Server and self.Server.is_connected():
            self.Server.close()

# 建立資料庫連接
db = Database(host="140.131.114.242", port=3306, dbname="113-113412", username="Beauty", pwd="6Eauty@110460")

# 獲取產品評語
def get_reviews_from_db():
    sql = "SELECT ReviewID, ReviewText FROM Reviews"  # 從 Reviews 表中獲取 ReviewID 和 ReviewText
    return db.getSqlData(sql)

# 獲取資料
reviews_data = get_reviews_from_db()

# 將資料轉換為 DataFrame
df = pd.DataFrame(reviews_data, columns=["id", "review"])

# 文字清理
df['review'] = df['review'].str.replace('[^a-zA-Z]', ' ', regex=True)  # 使用 regex=True 避免未來可能的錯誤
df['review'] = df['review'].str.lower()

# 向量化評語
vectorizer = CountVectorizer()
X = vectorizer.fit_transform(df['review'])

# 嘗試載入訓練好的模型
try:
    model = joblib.load('sentiment_model.pkl')
    print("模型加載成功")
except FileNotFoundError:
    print("模型尚未訓練，請訓練模型後再次運行此程序。")

    # 你需要提供標籤數據 y_train，長度應該與 X 的樣本數一致
    import numpy as np
    y_train = np.random.randint(0, 2, size=X.shape[0])  # 隨機生成 0 和 1 作為標籤，應根據實際數據來標記

    # 使用數據進行模型訓練
    model = MultinomialNB()
    model.fit(X, y_train)

    # 保存模型
    joblib.dump(model, 'sentiment_model.pkl')
    print("模型訓練完成並保存")

# 預測評分
df['predicted_rating'] = model.predict(X)

# 更新資料庫中的評分
def update_ratings_in_db(df):
    for idx, row in df.iterrows():
        # 更新 Reviews 表的 Rating 欄位
        sql = "UPDATE Reviews SET Rating = %s WHERE ReviewID = %s"
        db.runSql(sql, (row['predicted_rating'], row['id']))
        print(f"ReviewID: {row['id']} - Predicted Rating: {row['predicted_rating']}")  # 輸出每次更新

# 將預測的評分更新到資料庫
update_ratings_in_db(df)

# 關閉資料庫連接
db.close()
