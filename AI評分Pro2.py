import mysql.connector
import numpy as np
import random
from sklearn.feature_extraction.text import TfidfVectorizer

# 連接資料庫的詳細資訊
db_config = { 
    'host': "140.131.114.242",
    'port': 3306,
    'user': "Beauty",
    'password': "6Eauty@110460",
    'database': "113-113412"
}

# 連接資料庫
try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    print("成功連接到資料庫")
except mysql.connector.Error as err:
    print(f"錯誤: {err}")

# 計算加權分數
def calculate_weighted_score(tfidf_matrix, keywords, vectorizer):
    """根據 TF-IDF 分數和權重計算最終分數"""
    # 確保關鍵詞數量與特徵數量一致
    feature_names = vectorizer.get_feature_names_out()
    weights = np.zeros(len(feature_names))

    for kw, weight in keywords:
        if kw in feature_names:
            weights[np.where(feature_names == kw)[0][0]] = weight

    score = np.dot(tfidf_matrix.toarray(), weights)  # 計算加權總分
    return score.sum()

# 計算調整過的分數
def calculate_adjusted_score(tfidf_matrix, sentiment_score):
    """計算最終分數，將匹配度與情感分數結合"""
    score = tfidf_matrix.sum()

    # 重新定義分數範圍：將其轉換到 25-100 的範圍
    if score > 0:
        score = max(25, min((score * 100 / tfidf_matrix.sum()), 100))
    else:
        score = random.uniform(25, 50)  # 最低分數提高到 25-50 之間

    # 結合情感分數：調整情感分數權重並加入隨機變量
    final_score = (score + (sentiment_score + 1) * 50) / 2 + random.uniform(-5, 5)

    # 確保分數在1到100之間
    if final_score > 100:
        # 進行歸一化，將超過100的分數縮放回1-100範圍
        final_score = 100 - (final_score - 100) * 0.5  # 調整比例，避免分數大幅變動
    elif final_score < 1:
        final_score = 1  # 確保不低於1

    return final_score

# 查詢產品和評論資料
cursor.execute("SELECT product_id, product_name, review_content FROM Review")
reviews = cursor.fetchall()

# 初始化 TfidfVectorizer，適用於中文文本
vectorizer = TfidfVectorizer()

for review in reviews:
    product_id = review[0]
    product_name = review[1]
    review_content = review[2]
    
    # 使用 TF-IDF 處理評論內容
    tfidf_matrix = vectorizer.fit_transform([review_content])

    # 情感分析（假設 sentiment_score 為分析結果，1 代表正向，-1 代表負向）
    sentiment_score = random.choice([-1, 0, 1])

    # 假設的關鍵詞和權重（這裡需要你的關鍵詞提取邏輯）
    keywords = [("保濕", 0.8), ("控油", 0.6), ("持久", 0.7)]  # 請根據實際情況修改

    # 計算加權分數
    weighted_score = calculate_weighted_score(tfidf_matrix, keywords, vectorizer)

    # 計算調整過的最終分數
    final_score = calculate_adjusted_score(tfidf_matrix, sentiment_score)

    # 對每個膚質評估分數
    skin_types = ["乾性", "油性", "混合性", "敏感性"]
    skin_scores = {}

    for skin_type in skin_types:
        # 根據不同膚質給出不同的加權計算（這裡可以增加膚質相關的邏輯）
        skin_scores[skin_type] = final_score + random.uniform(-10, 10)  # 引入隨機小幅度變動

    # 檢查產品名稱以提高某些膚質的分數
    if "控油" in product_name:
        skin_scores["油性"] = max(skin_scores["油性"], final_score + 10)  # 油性膚質提高分數
    if "保濕" in product_name:
        skin_scores["乾性"] = max(skin_scores["乾性"], final_score + 10)  # 乾性膚質提高分數
    if "抗敏" in product_name:
        skin_scores["敏感性"] = max(skin_scores["敏感性"], final_score + 10)  # 敏感性膚質提高分數

    # 找到最匹配的膚質
    best_skin_type = max(skin_scores, key=skin_scores.get)
    best_score = skin_scores[best_skin_type]

    # 減去10分，並確保最終分數不會低於1
    best_score = max(best_score - 10, 1)

    # 四捨五入到小數點後兩位
    best_score = round(best_score, 2)

    # 更新資料庫
    try:
        update_query = """
            UPDATE Review 
            SET SkinTypeRating = %s, BestSkinType = %s 
            WHERE product_id = %s
        """
        cursor.execute(update_query, (f"{best_score:.2f}", best_skin_type, product_id))  # 確保分數轉為字符串，格式化為兩位小數
        conn.commit()

        print(f"Processing Product: {product_name}, Best Skin Type: {best_skin_type}, Score: {best_score:.2f}")

    except mysql.connector.Error as err:
        print(f"處理資料時發生錯誤: {err}")


# 關閉連接
cursor.close()
