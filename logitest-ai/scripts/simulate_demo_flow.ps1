param(
  [string]$BaseUrl = "http://localhost:3001",
  [string]$SessionId = "session-defense-demo",
  [string]$TraceId = "trace-defense-demo",
  [string]$UserId = "user-buyer-001"
)

$ErrorActionPreference = "Stop"

$headers = @{
  "x-session-id" = $SessionId
  "x-trace-id" = $TraceId
  "x-user-id" = $UserId
}

function Invoke-DemoRequest {
  param(
    [string]$Method,
    [string]$Path,
    [object]$Body = $null
  )

  $requestHeaders = $headers.Clone()
  $requestHeaders["x-request-id"] = "req-$([guid]::NewGuid().ToString("N").Substring(0, 12))"

  $parameters = @{
    Method = $Method
    Uri = "$BaseUrl$Path"
    Headers = $requestHeaders
  }

  if ($null -ne $Body) {
    $parameters["ContentType"] = "application/json"
    $parameters["Body"] = ($Body | ConvertTo-Json -Depth 8)
  }

  Invoke-RestMethod @parameters
}

Write-Host "Running LogiTest demo flow against $BaseUrl"

$login = Invoke-DemoRequest -Method Post -Path "/api/auth/login" -Body @{
  username = "buyer_001"
  password = "password123"
}

$search = Invoke-DemoRequest -Method Get -Path "/api/products?keyword=headphones"
$productId = $search.data.items[0].id

Invoke-DemoRequest -Method Post -Path "/api/cart/items" -Body @{
  productId = $productId
  quantity = 1
} | Out-Null

Invoke-DemoRequest -Method Get -Path "/api/cart" | Out-Null

$order = Invoke-DemoRequest -Method Post -Path "/api/orders" -Body @{}
$orderId = $order.data.orderId

Invoke-DemoRequest -Method Get -Path "/api/orders/$orderId" | Out-Null

Write-Host "Demo flow completed"
Write-Host "User: $($login.data.userId)"
Write-Host "Product: $productId"
Write-Host "Order: $orderId"
Write-Host "Session: $SessionId"
Write-Host "Trace: $TraceId"
