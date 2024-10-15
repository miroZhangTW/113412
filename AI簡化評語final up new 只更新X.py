import mysql.connector
import re

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

# 偏激字眼清單
extreme_words = [
    "幹(?!麻|嘛)",  # 這裡使用正則排除 "幹麻" 和 "幹嘛"
    "去死", "狗屎", "傻逼",
    "他媽的", "廢物", "白癡",
    "智障", "蠢貨", "死垃圾"
]

# 評語簡化 (提取產品信息)
def simplify_review(text):
    try:
        # 如果原始文本中中文字數少於 10，直接返回無效原因
        if len(re.findall(r'[\u4e00-\u9fff]', text)) < 10:
            return text, "X(原始評論過短)"

        # 檢查是否有偏激字眼
        for word in extreme_words:
            if word in text:
                return text, f"X(含有偏激字眼: {word})"

        # 如果文本過短，直接返回原始文本而不顯示無效原因
        if len(text) < 50:
            return text, None

        # 清理不必要的部分
        lines = [line for line in text.splitlines() if "大家好" not in line and "謝謝" not in line]
        cleaned_text = ' '.join(lines).strip()

        # 刪除括號中的文字
        cleaned_text = re.sub(r'\(.*?\)', '', cleaned_text)

        # 刪除不必要的標點符號
        cleaned_text = re.sub(r'^[,，.。…、]+', '', cleaned_text)
        cleaned_text = re.sub(r'[\.\@]{2,}', '', cleaned_text)
        cleaned_text = re.sub(r'(?<=\W)\w，', '', cleaned_text)
        cleaned_text = re.sub(r'[!?~]{2,}', '', cleaned_text)
        cleaned_text = re.sub(r'^[!?~.,，。]+', '', cleaned_text)

        # 確保處理後的文本長度
        if len(cleaned_text) < 50:
            return text, None

        # 提取產品相關信息
        product_info = []

        product_name_match = re.search(r'(?<=的)[^，。]+', cleaned_text)
        if product_name_match:
            product_info.append(product_name_match.group(0).strip())

        effectiveness_match = re.search(r'效果.*?[\。！]', cleaned_text)
        if effectiveness_match:
            product_info.append(effectiveness_match.group(0).strip())

        experience_match = re.search(r'使用.*?。', cleaned_text)
        if experience_match:
            product_info.append(experience_match.group(0).strip())

        # 組合為簡化評論
        summary = '，'.join(product_info)

        return summary, None  # 無錯誤

    except Exception as e:
        return text, f"X(處理失敗，原因: {e})"

# --- 使用示例 ---
if __name__ == "__main__":
    # 初始化連接資料庫
    db = Database(host="140.131.114.242", port=3306, dbname="113-113412", username="Beauty", pwd="6Eauty@110460")

    # 測試連接
    if db.test():
        print("成功連接到資料庫")
    else:
        print("無法連接到資料庫")

    # 查詢數據，只選取 SimplifiedReview 欄位以 "X" 開頭的資料
    try:
        results = db.getSqlData("SELECT review_content FROM Reviews WHERE SimplifiedReview LIKE 'X%'")
        for row in results:
            review_content = row[0]
            print(f"原始評論內容: {review_content}")
            simplified_review, invalid_reason = simplify_review(review_content)

            if invalid_reason:
                print(f"(X) 原因: {invalid_reason}")
                # 更新無效原因到資料庫
                db.runSql("UPDATE Reviews SET SimplifiedReview = %s WHERE review_content = %s", (invalid_reason, review_content))
            else:
                # 更新簡化評論到資料庫
                db.runSql("UPDATE Reviews SET SimplifiedReview = %s WHERE review_content = %s", (simplified_review, review_content))
                print(f"簡化評論: {simplified_review}\n")

    except mysql.connector.Error as err:
        print(f"查詢數據時發生錯誤: {err}")

    # 最後關閉連接
    db.close()
