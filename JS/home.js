// 選擇頭部元素
const header = document.querySelector('.header');
let lastScrollTop = 0; // 儲存上次滾動的位置

// 當窗口滾動時執行
window.addEventListener("scroll", function() {
    // 獲取當前滾動位置
    let currentScroll = window.pageYOffset || document.documentElement.scrollTop;

    // 判斷是向下滾動還是向上滾動
    if (currentScroll > lastScrollTop) {
        header.classList.add('hide'); // 向下滾動，隱藏頭部
    } else {
        header.classList.remove('hide'); // 向上滾動，顯示頭部
    }
    lastScrollTop = currentScroll <= 0 ? 0 : currentScroll; // 更新上次滾動位置
}, false);


//登入夏拉


// 初始化幻燈片索引
let currentIndex = 0;
const slides = document.querySelectorAll('#carousel img'); // 獲取所有幻燈片
const totalSlides = slides.length; // 幻燈片總數

// 顯示指定索引的幻燈片
function showSlide(index) {
    slides.forEach((slide, i) => {
        slide.classList.remove('active'); // 移除所有幻燈片的顯示
        if (i === index) {
            slide.classList.add('active'); // 添加當前幻燈片的顯示
        }
    });
}

// 搜索功能
function search() {
    const query = document.getElementById('searchInput').value.trim(); // 去除首尾空格
    if (query) {
        // 跳轉到相關產品頁面
        window.location.href = `http://beautybuddy.ddns.net/products?keyword=${encodeURIComponent(query)}`;
    } else {
        alert("請輸入有效的關鍵字"); // 提示用戶輸入有效的關鍵字
    }
}

// 顯示前一張幻燈片
function previousSlide() {
    currentIndex = (currentIndex === 0) ? totalSlides - 1 : currentIndex - 1; // 如果當前索引是0，則返回最後一張幻燈片
    showSlide(currentIndex); // 顯示前一張幻燈片
}

// 顯示下一張幻燈片
function nextSlide() {
    currentIndex = (currentIndex === totalSlides - 1) ? 0 : currentIndex + 1; // 如果當前索引是最後一張，則返回第一張
    showSlide(currentIndex); // 顯示下一張幻燈片
}

// 每3秒自動切換到下一張幻燈片
setInterval(nextSlide, 3000);

// 顯示彈出窗口（肌膚檢測）
function showPopup() {
    document.getElementById('overlay').style.display = 'flex'; // 將彈出窗口的顯示設為flex
}

// 隱藏彈出窗口
function hidePopup() {
    document.getElementById('overlay').style.display = 'none'; // 隱藏彈出窗口
}

// 選擇選項並改變顏色
function selectOption(button) {
    var selectedValue = button.value; // 獲取按鈕的值
    var buttons = button.parentNode.querySelectorAll('button'); // 獲取同一組中的所有按鈕
    buttons.forEach(function(btn) {
        // 根據選擇的按鈕改變背景顏色
        btn.style.backgroundColor = btn.value === selectedValue ? '#ff6f61' : '#ffcccb'; 
    });
}

// 計算肌膚類型
function calculateSkinType() {
    // 獲取選擇的敏感度、保濕度和油脂度
    var sensitivity = parseInt(document.querySelector('div:nth-child(2) .button-group button[style="background-color: rgb(255, 111, 97);"]').value);
    var hydration = parseInt(document.querySelector('div:nth-child(3) .button-group button[style="background-color: rgb(255, 111, 97);"]').value);
    var oiliness = parseInt(document.querySelector('div:nth-child(4) .button-group button[style="background-color: rgb(255, 111, 97);"]').value);

    var resultText; // 儲存結果文本
    // 根據選擇的數值來判斷膚質
    if (sensitivity <= 2 && hydration <= 2 && oiliness >= 4) {
        resultText = "您是敏感混合性肌膚，建議使用溫和且滋潤的保養品。";
    } else if (sensitivity <= 2 && hydration <= 2) {
        resultText = "您是敏感乾性肌膚，建議使用溫和且滋潤的保養品。";
    } else if (sensitivity <= 2 && oiliness <= 2) {
        resultText = "您是敏感油性肌膚，建議使用溫和且控油的保養品。";
    } else if (sensitivity <= 2) {
        resultText = "您是敏感肌膚，建議使用溫和的保養品。";
    } else if (hydration <= 2 && oiliness <= 2) {
        resultText = "您是乾性肌膚，建議使用高保濕的保養品。";
    } else if (hydration <= 2 && oiliness >= 4) {
        resultText = "您是混合性肌膚，建議使用平衡水油的保養品。";
    } else if (oiliness <= 2) {
        resultText = "您是油性肌膚，建議使用控油的保養品。";
    } else {
        resultText = "您是肌膚狀態正常，保持現有的保養方式即可。";
    }

    var output = "您的膚質檢測結果：" + resultText; // 組合結果文本
    var email = prompt("請輸入您的email:"); // 請求用戶輸入郵件

    document.getElementById("result").innerHTML = output; // 顯示結果
}
