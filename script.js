/*首頁*/

// 获取header元素
const header = document.querySelector('.header');

// 用于检测页面滚动方向的变量
let lastScrollTop = 0;

// 监听页面滚动事件
window.addEventListener("scroll", function() {
    let currentScroll = window.pageYOffset || document.documentElement.scrollTop;

    // 检测滚动方向
    if (currentScroll > lastScrollTop) {
        // 向下滚动时隐藏header
        header.classList.add('hide');
    } else {
        // 向上滚动时显示header
        header.classList.remove('hide');
    }
    lastScrollTop = currentScroll <= 0 ? 0 : currentScroll; // 修正iOS上的回弹效果
}, false);

let currentIndex = 0;
const slides = document.querySelectorAll('#carousel img');
const totalSlides = slides.length;

function showSlide(index) {
    slides.forEach((slide, i) => {
        slide.classList.remove('active');
        if (i === index) {
            slide.classList.add('active');
        }
    });
}

function search() {
    const query = document.getElementById('searchInput').value;
    // 执行搜索操作，例如显示搜索结果或者其他操作
    alert('您搜尋了: ' + query);
}

function previousSlide() {
    currentIndex = (currentIndex === 0) ? totalSlides - 1 : currentIndex - 1;
    showSlide(currentIndex);
}

function nextSlide() {
    currentIndex = (currentIndex === totalSlides - 1) ? 0 : currentIndex + 1;
    showSlide(currentIndex);
}

setInterval(nextSlide, 3000); // 每隔3秒切換到下一張圖片

function showPopup() {
    document.getElementById('overlay').style.display = 'flex';
}

function hidePopup() {
    document.getElementById('overlay').style.display = 'none';
}

function selectOption(button) {
    var selectedValue = button.value;
    var buttons = button.parentNode.querySelectorAll('button');
    buttons.forEach(function(btn) {
        btn.style.backgroundColor = btn.value === selectedValue ? '#ff6f61' : '#ffcccb';
    });
}

function calculateSkinType() {
    var selectedButtons = document.querySelectorAll('button[style="background-color: rgb(255, 111, 97);"]');
    var totalScore = 0;
    selectedButtons.forEach(function(btn) {
        totalScore += parseInt(btn.value);
    });
    var averageScore = totalScore / 3;

    var resultText;
    if (averageScore <= 2) {
        resultText = "您的皮膚狀態：非常敏感且非常乾燥或非常油膩";
    } else if (averageScore <= 3) {
        resultText = "您的皮膚狀態：敏感且乾燥或油膩";
    } else if (averageScore <= 4) {
        resultText = "您的皮膚狀態：敏感且稍微乾燥或稍微油膩";
    } else {
        resultText = "您的皮膚狀態：較不敏感且正常水分與油脂";
    }

    var email = prompt("請輸入您的email:");
    var output = "您的膚質檢測結果：" + resultText + "<br><br>根據您的膚質檢測，適合的產品有：<br>";
    // 在這裡添加適合的產品
    // output += "產品1<br>";
    // output += "產品2<br>";
    // output += "產品3<br>";
    document.getElementById("result").innerHTML = output;
}
