function toggleFavorite(product) {
    fetch('/add_favorite', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken') // 如果你有啟用 CSRF 防護，則需要這行
        },
        body: JSON.stringify({
            product_name: product.name,
            brand: product.brand,
            category: product.category,
            sizeprice: product.sizeprice,
            img_url: product.img
        })
    })
    .then(response => {
        if (response.ok) {
            alert('已收藏此產品！');
        } else {
            return response.json().then(errorData => {
                alert(`${errorData.message}`);
            });
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('請先登入即可收藏!!');
    });
}


// 獲取 CSRF 令牌的輔助函數（如有需要）
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Check if this cookie string begins with the desired name
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
