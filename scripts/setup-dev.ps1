# Mem-Switch 开发环境初始化 (Windows PowerShell)

Write-Host "=== Mem-Switch 开发环境初始化 ===" -ForegroundColor Cyan

# 检查依赖
Write-Host "检查 Node.js..." -ForegroundColor Yellow
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "错误: 需要 Node.js (>=18)" -ForegroundColor Red
    exit 1
}
$nodeVersion = (node -v) -replace 'v',''
if ([version]$nodeVersion -lt [version]"18.0.0") {
    Write-Host "错误: Node.js >= 18 required" -ForegroundColor Red
    exit 1
}

Write-Host "检查 Python..." -ForegroundColor Yellow
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "错误: 需要 Python (>=3.10)" -ForegroundColor Red
    exit 1
}

Write-Host "检查 Conda..." -ForegroundColor Yellow
if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    Write-Host "错误: 需要 Miniconda/Anaconda" -ForegroundColor Red
    exit 1
}

Write-Host "检查 Rust..." -ForegroundColor Yellow
if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
    Write-Host "警告: Rust 未安装，请安装 https://rustup.rs" -ForegroundColor DarkYellow
}

Write-Host "检查 Ollama..." -ForegroundColor Yellow
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    Write-Host "警告: Ollama 未安装，请安装 https://ollama.com" -ForegroundColor DarkYellow
}

# 安装前端依赖
Write-Host "安装前端依赖..." -ForegroundColor Yellow
Set-Location frontend
npm install
Set-Location ..

# 创建后端 conda 环境
Write-Host "创建/激活后端 conda 环境 (mem-switch)..." -ForegroundColor Yellow
$envCreated = $false
conda create -n mem-switch python=3.10 -y 2>$null
$envCreated = $?
conda activate mem-switch
pip install -r backend/requirements.txt

Write-Host ""
Write-Host "=== 初始化完成 ===" -ForegroundColor Green
Write-Host ""
Write-Host "启动开发模式:" -ForegroundColor Cyan
Write-Host ""
Write-Host "方式1 - 启动后端和前端 (浏览器访问 http://localhost:5173):"
Write-Host '  conda activate mem-switch' -ForegroundColor Gray
Write-Host '  cd backend; uvicorn main:app --host 127.0.0.1 --port 8765 --reload' -ForegroundColor Gray
Write-Host "  (新终端) cd frontend; npm run dev" -ForegroundColor Gray
Write-Host ""
Write-Host "方式2 - 启动完整 Tauri 桌面应用:"
Write-Host '  conda activate mem-switch' -ForegroundColor Gray
Write-Host '  cd backend; uvicorn main:app --host 127.0.0.1 --port 8765 --reload' -ForegroundColor Gray
Write-Host "  (新终端) npm run tauri dev" -ForegroundColor Gray