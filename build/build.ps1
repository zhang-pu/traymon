# TrayMon 一键打包脚本（Windows 上执行）
# 用法：PowerShell 里执行  .\build\build.ps1
# 产物：..\release\TrayMon.exe（单文件，无控制台窗口）

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $here
Set-Location $root

Write-Host "== 检查 Python ==" -ForegroundColor Cyan
python --version

Write-Host "== 安装依赖 ==" -ForegroundColor Cyan
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

Write-Host "== 清理旧的打包目录 ==" -ForegroundColor Cyan
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue build\TrayMon
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue dist
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue release

Write-Host "== 打包（单文件 / 无控制台）==" -ForegroundColor Cyan
python -m PyInstaller --onefile --windowed --name TrayMon `
  --clean --noconfirm system_monitor.py

Write-Host "== 收集产物 ==" -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path release | Out-Null
Copy-Item -Force dist\TrayMon.exe release\TrayMon.exe

$size = [math]::Round((Get-Item release\TrayMon.exe).Length / 1MB, 1)
Write-Host ""
Write-Host "完成：$root\release\TrayMon.exe  ($size MB)" -ForegroundColor Green
Write-Host "（release/ 已在 .gitignore 中，不会进 Git 仓库）"
