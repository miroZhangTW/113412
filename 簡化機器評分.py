import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
import joblib
import mysql.connector
from transformers import pipeline
import logging

# 設定日誌
logging.basicConfig(filename='review_update.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# 評語簡化 (摘要)
def simplify_review(text):
    summarizer = pipeline("summarization", model="google-t5/t5-small")
    summary = summarizer(text, max_length=30, min_length=5)
    return summary[0]['summary_text']

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
        if self.Server is None or not self.Server.is_connected():
            self.Server = mysql.connector.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )

    def getSqlData(self, sql):
        self.setServer()
        cursor = self.Server.cursor()
        try:
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()

    def runSql(self, sql, data=None):
        self.setServer()
        cursor = self.Server.cursor()
        try:
            if data is None:
                cursor.execute(sql)
            else:
                cursor.execute(sql, data)
            self.Server.commit()
        finally:
            cursor.close()

    def close(self):
        if self.Server and self.Server.is_connected():
            self.Server.close()

# 建立資料庫連接
db = Database(host="140.131.114.242", port=3306, dbname="113-113412", username="Beauty", pwd="6Eauty@110460")

# 獲取產品評語
def get_reviews_from_db():
    sql = "SELECT ReviewID, ReviewText, ProductName FROM Reviews"
    return db.getSqlData(sql)

# 獲取資料
reviews_data = get_reviews_from_db()

# 將資料轉換為 DataFrame
df = pd.DataFrame(reviews_data, columns=["id", "review", "product"])

# 文字清理
df['review'] = df['review'].str.replace('[^a-zA-Z]', ' ', regex=True)
df['review'] = df['review'].str.lower()

# 評語簡化 (摘要)
df['simplified_review'] = df['review'].apply(simplify_review)

# 載入模型和向量化器
model = joblib.load('sentiment_model.pkl')
vectorizer = joblib.load('vectorizer.pkl')

# 向量化簡化評語
X = vectorizer.transform(df['simplified_review'])

# 預測評分
df['predicted_rating'] = model.predict(X)

# 更新資料庫中的簡化評語和 AI 評分（每筆資料都立即更新）
def update_ratings_in_db(df):
    for idx, row in df.iterrows():
        try:
            sql = "UPDATE Reviews SET Rating = %s, ReviewText = %s, SimplifiedReview = %s WHERE ReviewID = %s"
            db.runSql(sql, (row['predicted_rating'], row['review'], row['simplified_review'], row['id']))
            logging.info(f"成功更新 ReviewID: {row['id']}")
        except Exception as e:
            logging.error(f"更新失敗 ReviewID: {row['id']} - 錯誤訊息: {e}")

# 批量更新，提升效率（可選）
def batch_update_ratings_in_db(df):
    # 構造批量更新 SQL
    updates = []
    for idx, row in df.iterrows():
        updates.append((row['predicted_rating'], row['review'], row['simplified_review'], row['id']))

    try:
        sql = "UPDATE Reviews SET Rating = %s, ReviewText = %s, SimplifiedReview = %s WHERE ReviewID = %s"
        db.runSql(sql, updates)
        logging.info("批量更新成功")
    except Exception as e:
        logging.error(f"批量更新失敗 - 錯誤訊息: {e}")

# 將預測的評分和簡化的評語更新到資料庫
update_ratings_in_db(df)

# 關閉資料庫連接
db.close()
