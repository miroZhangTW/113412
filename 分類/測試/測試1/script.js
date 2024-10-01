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

// 搜索功能
function search() {
    const query = document.getElementById('searchInput').value; // 獲取輸入的搜索內容
    alert('您搜尋了: ' + query); // 彈出提示顯示搜索內容
}
// 隱藏彈出窗口
function hidePopup() {
    document.getElementById('overlay').style.display = 'none'; // 隱藏彈出窗口
}