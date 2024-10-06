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