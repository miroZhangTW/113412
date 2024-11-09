import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

# 设置请求头
headers = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'}

# 获取品牌列表页
url = "https://www.cosme.net.tw/brand-list"
response = requests.get(url, headers=headers)
response.encoding = 'utf8'
soup = BeautifulSoup(response.text, 'html.parser')

# 用户输入希望搜索的品牌名称和产品类别关键字
search_brand_name = input("请输入希望搜索的品牌名称: ")
search_product_category = input("请输入希望搜索的产品类别关键字: ")

# 初始化一个空的 DataFrame 用于存储结果
columns = ["品牌名称", "产品名称", "容量及价格", "类别", "评分", "使用资讯", "评论内容"]
df = pd.DataFrame(columns=columns)

# 找到所有品牌
brand_elements = soup.select(f'#brands-list .uc-brand-list-brand')

# 遍历每个品牌，找到匹配的品牌名称
for brand in brand_elements:
    brand_name = brand.text.strip()
    if search_brand_name in brand_name:
        print("品牌:", brand_name)

        # 获取品牌的链接
        minor_link = brand.find(class_="uc-minor-link")
        if minor_link:
            href_attribute = minor_link.get('href', 'N/A')

            # 提取品牌ID
            brand_id_match = re.search(r'/brands/(\d+)', href_attribute)
            if brand_id_match:
                brand_id = brand_id_match.group(1)
                print("Brand ID:", brand_id)

                # 构建评论网址
                review_url = f"https://www.cosme.net.tw/brands/{brand_id}/reviews"
                print("评论网址:", review_url)

                # 第二段程式碼
                base_url_template = f"https://www.cosme.net.tw/brands/{brand_id}/reviews?page="
                headers = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'}

                review_number = 0

                page_number = 1
                base_url = base_url_template

                while True:
                    url = f"{base_url}{page_number}"
                    response = requests.get(url, headers=headers)
                    response.encoding = 'utf8'

                    soup = BeautifulSoup(response.text, 'html.parser')

                    # 检查是否有评论
                    reviews = soup.find_all(class_="uc-review uc-review-with-product")
                    if not reviews:
                        print(f"品牌 {brand_id} 没有更多评论，停止执行。")
                        break

                    for review in reviews:
                        # 删除包含其他属性的元素
                        review_attributes = review.find(class_="review-attributes")
                        if review_attributes:
                            review_attributes.extract()

                        # 提取产品信息
                        product_info = review.find(class_="product-info")
                        product_brand = product_info.find(class_="brand-name").text.strip()
                        product_name = product_info.find(class_="product-name").text.strip()
                        product_price_element = product_info.find(class_="product-info-others")
                        product_price = product_price_element.text.strip() if product_price_element else "N/A"
                        product_category_element = product_info.find(class_="product-info-attr")
                        product_category = product_category_element.text.strip() if product_category_element else "N/A"

                        # 根据输入的产品类别关键字进行筛选
                        if search_product_category in product_category:
                            review_score_element = review.find(class_="review-score")
                            review_score = review_score_element.text.strip() if review_score_element else "N/A"

                            # 初始化一个字典用于存储评论信息
                            review_data = {
                                "品牌名称": product_brand,
                                "产品名称": product_name,
                                "容量及价格": product_price,
                                "类别": product_category,
                                "评分": review_score,
                                "使用资讯": "",
                                "评论内容": ""
                            }

                            # 提取评论内容
                            content_link = review.find(class_="review-content-top")
                            if content_link:
                                content_url = content_link.get('href', 'N/A')
                                full_content_url = f"https://www.cosme.net.tw{content_url}"

                                # 访问评价页面
                                response = requests.get(full_content_url, headers=headers)
                                response.encoding = 'utf8'
                                review_soup = BeautifulSoup(response.text, 'html.parser')

                                # 打印使用资讯
                                review_attributes = review_soup.find(class_="review-attributes")
                                if review_attributes:
                                    other_attributes_elements = review_attributes.find_all(class_="other-attributes")
                                    review_data["使用资讯"] = "\n".join([attr.text.strip() for attr in other_attributes_elements])
                                else:
                                    review_data["使用资讯"] = "N/A"

                                # 提取评论内容
                                review_content = review_soup.find(class_="review-content")
                                if review_content:
                                    # 去掉包含class="other-attributes"的内容
                                    other_attributes_elements = review_content.find_all(class_="other-attributes")
                                    for other_attributes in other_attributes_elements:
                                        other_attributes.extract()
                                    review_data["评论内容"] = review_content.text.strip()

                            # 将数据追加到 DataFrame
                            df = pd.concat([df, pd.DataFrame([review_data])], ignore_index=True)

                    # 如果到最后一页，则结束循环
                    if "没有更多页面的标志" in response.text:
                        break

                    page_number += 1

# 将 DataFrame 导出到 Excel
df.to_excel("reviews.xlsx", index=False)
print("数据已导出到 reviews.xlsx")
