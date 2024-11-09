'''
使用資訊和評論內容分開

请输入希望搜索的品牌名称: 1028
请输入希望搜索的产品类别关键字: 粉底
品牌: 1028
Brand ID: 441
评论网址: https://www.cosme.net.tw/brands/441/reviews
品牌名称: 1028
产品名称: 極上鏡 柔光超磁水粉底SPF45 PA++
容量及价格: 30ml / NT$ 530
类别: 粉底液
评分: 2
使用资讯:
・色號： 110柔白
・效果： - -
・體驗方式： 正品容量/藥妝店
・使用季節： 秋
・使用環境： 換季
评论内容: 圖片為相機錄影截圖上面有時間 給各位姐妹參考本人膚質T區會出油兩頰偏乾使用色號為柔白早上6點多打完粉底的樣子妝感不是很精緻但遮瑕力蠻好的上完蜜粉後妝感明顯好很多到了下午四點中間都沒補過蜜粉的情況下持妝能力是不錯的很控油但相對的兩夾乾到有點起皮並且這款粉底液會讓我長痘痘後置相機更清楚了T區會出油的地方沒問題但兩頰跟下巴都乾到有一點一點白白的像芝麻粒並且肉眼可見的讓我爆了幾顆痘痘感覺這款粉底液適合油皮的肌膚以上給大家參考
'''
import requests
from bs4 import BeautifulSoup
import re

# 第一段程式碼
url = "https://www.cosme.net.tw/brand-list"
headers = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'}
response = requests.get(url, headers=headers)
response.encoding = 'utf8'

soup = BeautifulSoup(response.text, 'html.parser')

# 让用户输入希望搜索的品牌名称
search_brand_name = input("请输入希望搜索的品牌名称: ")
# 让用户输入希望搜索的产品类别关键字
search_product_category = input("请输入希望搜索的产品类别关键字: ")

# 找到 id="brands-list" 中指定品牌名称的所有 class="uc-brand-list-brand" 元素
brand_elements = soup.select(f'#brands-list .uc-brand-list-brand')

# 遍历每个元素并找到匹配的品牌名称
for brand in brand_elements:
    brand_name = brand.text.strip()
    if search_brand_name in brand_name:
        print("品牌:", brand_name)

        # 找到每个 class="uc-brand-list-brand" 元素中的 class="uc-minor-link" 的元素
        minor_link = brand.find(class_="uc-minor-link")

        # 如果找到了 class="uc-minor-link" 元素，提取并列印 href 属性
        if minor_link:
            href_attribute = minor_link.get('href', 'N/A')

            # 使用正则表达式提取 Minor Link Href 中的品牌 ID
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

                            # 打印产品信息
                            print("品牌名称:", product_brand)
                            print("产品名称:", product_name)
                            print("容量及价格:", product_price)
                            print("类别:", product_category)
                            print("评分:", review_score)
                           

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
                                print("使用资讯:")
                                review_attributes = review_soup.find(class_="review-attributes")
                                if review_attributes:
                                    other_attributes_elements = review_attributes.find_all(class_="other-attributes")
                                    for other_attributes in other_attributes_elements:
                                        other_attributes_text = other_attributes.text.strip()
                                        print(other_attributes_text)
                                else:
                                    print("N/A")

                                # 提取评论内容
                                review_content = review_soup.find(class_="review-content")
                                if review_content:
                                    # 去掉包含class="other-attributes"的内容
                                    other_attributes_elements = review_content.find_all(class_="other-attributes")
                                    for other_attributes in other_attributes_elements:
                                        other_attributes.extract()
                                    review_text = review_content.text.strip()
                                    print("评论内容:", review_text)

                    # 如果到最后一页，则结束循环
                    if "没有更多页面的标志" in response.text:
                        break

                    page_number += 1
