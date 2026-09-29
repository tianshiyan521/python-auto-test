# ============================================
# DI助手 设备ID 一键修改脚本
# 功能：修改 MAC地址、MachineGuid、设备名
# 用法：右键 → 使用PowerShell运行（管理员）
# ============================================

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "DI设备ID修改工具"

# 检查管理员权限
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "[错误] 请右键此脚本 → 以管理员身份运行！" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}

Write-Host "╔══════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   DI助手 设备ID 批量修改工具 v1.0   ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── 1. 生成新的设备ID ──
$newMAC = ("{0:X2}{1:X2}{2:X2}{3:X2}{4:X2}{5:X2}" -f (Get-Random -Min 0 -Max 255), (Get-Random -Min 0 -Max 255), (Get-Random -Min 0 -Max 255), (Get-Random -Min 0 -Max 255), (Get-Random -Min 0 -Max 255), (Get-Random -Min 0 -Max 255))
$newGuid = [guid]::NewGuid().ToString()
$newPCName = "DESKTOP-" + -join ((65..90) | Get-Random -Count 6 | ForEach-Object { [char]$_ })

Write-Host "[信息] 即将修改以下设备标识：" -ForegroundColor Yellow
Write-Host "  新 MAC 地址   : $newMAC" -ForegroundColor White
Write-Host "  新 MachineGuid: $newGuid" -ForegroundColor White
Write-Host "  新计算机名    : $newPCName" -ForegroundColor White
Write-Host ""

$confirm = Read-Host "确认修改？(输入 Y 继续，其他键取消)"
if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "[取消] 已退出，未做任何修改。" -ForegroundColor Gray
    Read-Host "按任意键退出"
    exit 0
}

# ── 备份当前值 ──
$backupDir = "$env:TEMP\DI_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

$currentMAC = (Get-NetAdapter -Name "以太网" -ErrorAction SilentlyContinue).MacAddress
$currentGuid = (Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Cryptography" -Name "MachineGuid" -ErrorAction SilentlyContinue).MachineGuid
$currentPCName = $env:COMPUTERNAME

@"
原始配置备份：
MAC地址   = $currentMAC
MachineGuid = $currentGuid
计算机名   = $currentPCName
备份时间   = $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
"@ | Out-File -FilePath "$backupDir\backup.txt" -Encoding UTF8

Write-Host "[备份] 原始配置已保存到: $backupDir\backup.txt" -ForegroundColor Green
Write-Host ""

# ── 2. 修改 MAC 地址 ──
Write-Host "[1/3] 正在修改 MAC 地址..." -ForegroundColor Cyan

$adapterKey = "HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4D36E972-E325-11CE-BFC1-08002BE10318}"
$subKeys = Get-ChildItem -Path $adapterKey -ErrorAction SilentlyContinue
$targetKey = ""

foreach ($key in $subKeys) {
    $desc = (Get-ItemProperty -Path $key.PSPath -Name "DriverDesc" -ErrorAction SilentlyContinue).DriverDesc
    if ($desc -like "*Realtek*2.5*") {
        $targetKey = $key.PSPath
        break
    }
}

if ($targetKey -ne "") {
    # 写入新MAC到注册表
    Set-ItemProperty -Path $targetKey -Name "NetworkAddress" -Value $newMAC -Type String -Force
    Write-Host "  [OK] MAC地址已写入注册表: $newMAC" -ForegroundColor Green

    # 禁用再启用网卡
    Write-Host "  [执行] 正在重启网卡..." -ForegroundColor Yellow
    Disable-NetAdapter -Name "以太网" -Confirm:$false
    Start-Sleep -Seconds 2
    Enable-NetAdapter -Name "以太网" -Confirm:$false
    Start-Sleep -Seconds 3

    # 验证
    $verifyMAC = (Get-NetAdapter -Name "以太网").MacAddress
    if ($verifyMAC -eq $newMAC) {
        Write-Host "  [验证] MAC已生效: $verifyMAC" -ForegroundColor Green
    } else {
        Write-Host "  [警告] MAC可能未生效，请手动重启网卡或电脑后检查" -ForegroundColor Yellow
    }
} else {
    Write-Host "  [错误] 未找到Realtek网卡，跳过MAC修改" -ForegroundColor Red
}

Write-Host ""

# ── 3. 修改 MachineGuid ──
Write-Host "[2/3] 正在修改 MachineGuid..." -ForegroundColor Cyan
try {
    Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Cryptography" -Name "MachineGuid" -Value $newGuid -Force
    $verifyGuid = (Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Cryptography" -Name "MachineGuid").MachineGuid
    Write-Host "  [OK] MachineGuid已修改: $verifyGuid" -ForegroundColor Green
} catch {
    Write-Host "  [错误] MachineGuid修改失败: $_" -ForegroundColor Red
}

Write-Host ""

# ── 4. 修改计算机名 ──
Write-Host "[3/3] 正在修改计算机名..." -ForegroundColor Cyan
try {
    Rename-Computer -NewName $newPCName -Force
    Write-Host "  [OK] 计算机名已改为: $newPCName（重启生效）" -ForegroundColor Green
} catch {
    Write-Host "  [错误] 计算机名修改失败: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "╔══════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║          修改完成！                  ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "  新 MAC  : $newMAC"
Write-Host "  新 GUID : $newGuid"
Write-Host "  新设备名: $newPCName"
Write-Host "  备份文件: $backupDir\backup.txt"
Write-Host ""
Write-Host "[提示] 建议重启电脑后再打开DI助手测试" -ForegroundColor Yellow
Write-Host ""
Read-Host "按任意键退出"
