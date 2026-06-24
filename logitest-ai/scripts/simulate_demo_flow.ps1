param(
    [string]$BaseUrl = "http://localhost:3001",
    [string]$SessionId = "session-demo-001"
)

$ErrorActionPreference = "Stop"

$headers = @{
    "x-session-id" = $SessionId
    "x-trace-id" = "trace-demo-001"
    "x-request-id" = "req-demo-001"
    "x-user-id" = "user-buyer-001"
}

Write-Host "1. Login"
$login = Invoke-RestMethod `
    -Method Post `
    -Uri "$BaseUrl/api/auth/login" `
    -Headers $headers `
    -ContentType "application/json" `
    -Body (@{ username = "buyer_001"; password = "password123" } | ConvertTo-Json)

Write-Host "2. Search products"
$search = Invoke-RestMethod `
    -Method Get `
    -Uri "$BaseUrl/api/products?keyword=headphones" `
    -Headers $headers

$productId = $search.data.items[0].id

Write-Host "3. Add to cart: $productId"
$cart = Invoke-RestMethod `
    -Method Post `
    -Uri "$BaseUrl/api/cart/items" `
    -Headers $headers `
    -ContentType "application/json" `
    -Body (@{ productId = $productId; quantity = 1 } | ConvertTo-Json)

Write-Host "4. Read cart"
$cartDetail = Invoke-RestMethod `
    -Method Get `
    -Uri "$BaseUrl/api/cart" `
    -Headers $headers

Write-Host "5. Create order"
$order = Invoke-RestMethod `
    -Method Post `
    -Uri "$BaseUrl/api/orders" `
    -Headers $headers `
    -ContentType "application/json" `
    -Body (@{} | ConvertTo-Json)

$orderId = $order.data.orderId

Write-Host "6. Read order detail with chained orderId: $orderId"
$orderDetail = Invoke-RestMethod `
    -Method Get `
    -Uri "$BaseUrl/api/orders/$orderId" `
    -Headers $headers

[PSCustomObject]@{
    userId = $login.data.userId
    productId = $productId
    cartId = $cartDetail.data.cartId
    orderId = $orderId
    orderStatus = $orderDetail.data.status
    total = $orderDetail.data.total
} | ConvertTo-Json
