document.addEventListener('DOMContentLoaded', () => {
    // 選擇頭部元素
    const header = document.querySelector('.header');
    if (!header) {
        console.error('Header element not found!');
    }
    
    let lastScrollTop = 0; // 儲存上次滾動的位置



    // 隱藏彈出窗口
    document.getElementById('overlay').style.display = 'none'; // 確保在頁面加載時隱藏



    // 當窗口滾動時執行
    window.addEventListener("scroll", function() {
        let currentScroll = window.pageYOffset || document.documentElement.scrollTop;

        if (currentScroll > lastScrollTop) {
            header.classList.add('hide'); // 向下滾動，隱藏頭部
        } else {
            header.classList.remove('hide'); // 向上滾動，顯示頭部
        }
        lastScrollTop = currentScroll <= 0 ? 0 : currentScroll; // 更新上次滾動位置
    }, false);

    // 初始化幻燈片索引
    let currentIndex = 0;
    const slides = document.querySelectorAll('#carousel img');
    const totalSlides = slides.length;

    if (totalSlides === 0) {
        console.error('No slides found in the carousel!');
    }

    // 顯示指定索引的幻燈片
    function showSlide(index) {
        slides.forEach((slide, i) => {
            slide.classList.remove('active');
            if (i === index) {
                slide.classList.add('active');
            }
        });
    }

    // 搜索功能
    function search() {
        const query = document.getElementById('searchInput').value.trim();
        if (query) {
            window.location.href = `http://beautybuddy.ddns.net/products?keyword=${encodeURIComponent(query)}`;
        } else {
            alert("請輸入有效的關鍵字");
        }
    }

    // 顯示前一張幻燈片
    function previousSlide() {
        currentIndex = (currentIndex === 0) ? totalSlides - 1 : currentIndex - 1;
        showSlide(currentIndex);
    }

    // 顯示下一張幻燈片
    function nextSlide() {
        currentIndex = (currentIndex === totalSlides - 1) ? 0 : currentIndex + 1;
        showSlide(currentIndex);
    }

    // 每3秒自動切換到下一張幻燈片
    setInterval(nextSlide, 3000);
});

// 顯示彈出窗口（肌膚檢測）
function showPopup() {
    document.getElementById('overlay').style.display = 'flex';
}

// 隱藏彈出窗口
// 隱藏彈出窗口
function hidePopup() {
    document.getElementById('overlay').style.display = 'none';
    sensitivity = null;
    hydration = null;
    oiliness = null;
    const buttonGroups = document.querySelectorAll('.button-group');
    buttonGroups.forEach(group => {
        const buttons = group.querySelectorAll('button');
        buttons.forEach(btn => btn.classList.remove('selected'));
    });
    document.getElementById('result').innerText = '';

    // 清空推薦區域的內容
    document.getElementById('recommendations').innerHTML = '';
}


// 選擇選項並改變顏色
let sensitivity = null;
let hydration = null;
let oiliness = null;

function selectOption(button, category) {
    const buttons = document.querySelectorAll(`#${category}-group button`);
    buttons.forEach(btn => btn.classList.remove('selected'));
    button.classList.add('selected');

    if (category === 'sensitivity') sensitivity = button.value;
    if (category === 'hydration') hydration = button.value;
    if (category === 'oiliness') oiliness = button.value;
}

// 計算肌膚類型
// 計算肌膚類型
function calculateSkinType() {
    if (sensitivity && hydration && oiliness) {
        let resultText;

        // 判斷膚質類型
        if (sensitivity <= 2 && hydration <= 2 && oiliness >= 4) {
            resultText = "您是敏感混合性肌膚，建議使用溫和且滋潤的產品。";
        } else if (sensitivity <= 2 && hydration <= 2) {
            resultText = "您是敏感乾性肌膚，建議使用溫和且滋潤的產品。";
        } else if (sensitivity <= 2 && oiliness <= 2) {
            resultText = "您是敏感油性肌膚，建議使用溫和且控油的產品。";
        } else if (sensitivity <= 2) {
            resultText = "您是稍敏感但正常肌膚，建議使用溫和的產品。";
        } else if (hydration <= 2 && oiliness <= 2) {
            resultText = "您是乾性肌膚，建議使用高保濕的產品。";
        } else if (hydration <= 2 && oiliness >= 4) {
            resultText = "您是混合性肌膚，建議使用平衡水油的產品。";
        } else if (oiliness <= 2) {
            resultText = "您是油性肌膚，建議使用控油的產品。";
        } else if (sensitivity > 2 && hydration > 2 && oiliness > 2) {
            resultText = "您的膚質非常正常，保持現有的保養方式即可。你膚質很正常都很適合哦!!";
        } else {
            resultText = "您是肌膚狀態正常，保持現有的保養方式即可。";
        }

        // 更新結果顯示
        let output = "您的膚質檢測結果：" + resultText;
        document.getElementById('result').innerText = output;

        // 發送數據到後端以獲取推薦
        fetch('/get_recommendations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                result: resultText
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.recommendations && data.recommendations.length > 0) {
                let recommendations = data.recommendations;
                let recommendationsHtml = "<h3>推薦產品：</h3><div class='card-container'>";
                recommendations.forEach(item => {
                    let brand = item.brand_name || '未知品牌';
                    let product = item.product_name || '未知產品';
                    let size = item.size || '未知尺寸';
                    let price = item.price ? `$${item.price}` : '未知價格';
                    let imageUrl = item.image_url || 'default_image_url.jpg'; // 使用一個預設圖片

                    const productSlug = product.toLowerCase().replace(/\s+/g, '-'); // 將產品名稱轉為小寫並用連字符替換空格
                    recommendationsHtml += `
                        <a href="/product_detail/${productSlug}" class="card">
                            <img src="${imageUrl}" alt="${product}" class="product-image">
                            <h4>${brand}</h4>
                            <p>${product}</p>
                            <p>尺寸：${size}</p>
                            <p>價格：${price}</p>
                        </a>`;
                });
                recommendationsHtml += "</div>";
                document.getElementById('recommendations').innerHTML = recommendationsHtml;
            } else {
                document.getElementById('recommendations').innerHTML = "<p>您的膚質目前都很適合!持續保持</p>";
            }
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('recommendations').innerHTML = "<p>無法獲取推薦產品，請稍後再試。</p>";
        });

        // 發送膚質數據到後端的 Users 表
        fetch('/submit_skin_test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                sensitivity: sensitivity,
                hydration: hydration,
                oiliness: oiliness,
                result: resultText
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('數據成功提交至後端:', data);
        })
        .catch(error => {
            console.error('提交失敗:', error);
        });

    } else {
        alert('請選擇所有選項後再提交！');
    }
}


// 防止表單默認提交行為（避免按 Enter 鍵觸發 GET 請求）
const skinTestForm = document.getElementById('skinTestForm');
if (skinTestForm) {
    skinTestForm.addEventListener('submit', function(event) {
        event.preventDefault();
        calculateSkinType();
    });
}

// 假設你的選項按鈕會添加 'selected' 類名
document.querySelectorAll('.button-group button').forEach(button => {
    button.addEventListener('click', function() {
        const group = this.parentElement.id.split('-')[0];
        const buttons = document.querySelectorAll(`#${group}-group button`);
        buttons.forEach(btn => btn.classList.remove('selected'));
        this.classList.add('selected');
    });
});

