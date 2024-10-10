# 定義膚質與相關的中文關鍵詞及其權重
skin_type_keywords = {
    '乾性': [('保濕', 2), ('滋潤', 2), ('修護', 1), ('舒緩', 1)],
    '油性': [('控油', 2), ('清爽', 1), ('不致痘', 2), ('輕薄', 1)],
    '混合性': [('平衡', 1), ('輕薄', 1), ('保濕', 1), ('清爽', 1)],
    '敏感性': [('溫和', 2), ('無香料', 2), ('抗過敏', 1), ('修復舒緩', 1)]
}

# 在處理數據時，為每個產品對所有膚質都生成分數
for row in results:
    product_id, product_name, usage_info, effect, review_content, simplified_review = row
    combined_text = f"{product_name} {usage_info} {effect} {review_content} {simplified_review}"
    
    # 對每個膚質生成分數
    skin_type_results = {}
    for skin_type, keywords in skin_type_keywords.items():
        reviews = [combined_text]  # 將評論放入列表中
        tfidf_matrix = calculate_tfidf_score(reviews, keywords)
        score = calculate_weighted_score(tfidf_matrix, keywords)
        skin_type_results[skin_type] = max(score.sum(), 1)  # 強制最小分數為1

    # 將分數標準化並結合情感分析
    normalized_scores = normalize_scores(list(skin_type_results.values()))
    sentiment_score = calculate_sentiment_score(combined_text)
    sentiment_score = (sentiment_score + 1) * 50  # 將範圍調整到 0-100

    # 最終結果
    final_scores = {skin_type: (ns * 0.7 + sentiment_score * 0.3) for skin_type, ns in zip(skin_type_results.keys(), normalized_scores)}
    
    # 將每個膚質的分數輸出並存入資料庫
    for skin_type, final_score in final_scores.items():
        print(f"Processing Product: {product_name}, Skin Type: {skin_type}, Score: {final_score:.2f}")
        
        # 將每個膚質的分數更新到資料庫
        update_query = """
            UPDATE Review 
            SET SkinTypeRating = %s 
            WHERE product_id = %s AND BestSkinType = %s
        """
        db.runSql(update_query, (final_score, product_id, skin_type))
