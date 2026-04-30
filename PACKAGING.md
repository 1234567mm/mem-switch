# Mem-Switch 打包指南

## 支持的平台

| 平台 | 架构 | 状态 | 安装包格式 | 构建方式 |
|------|------|------|-----------|----------|
| Windows | x86_64 | ✅ 已完成 | exe (需 Windows 生成 NSIS) | 本地/交叉编译 |
| Windows | ARM64 | ✅ 已完成 | exe | 交叉编译 (cargo-xwin) |
| Linux | x86_64 | ✅ 已完成 | AppImage, .deb | 本地构建 |
| Linux | ARM64 | 🔲 待构建 | AppImage, .deb | 本地构建 |
| macOS | x86_64 | ✅ 已完成 | .app | GitHub Actions |
| macOS | ARM64 | ✅ 已完成 | .app | GitHub Actions |
| macOS | Universal | ✅ 已完成 | .app (双架构) | GitHub Actions |

---

## GitHub Actions 自动构建（推荐）

使用 GitHub Actions 进行跨平台自动构建：

### 触发构建

**方式 1：推送版本标签**
```bash
# 编辑版本号
vim src-tauri/Cargo.toml

# 创建并推送标签
git tag v0.1.0
git push origin v0.1.0
```

**方式 2：使用发布脚本**
```bash
./scripts/release.sh 0.1.0
```

**方式 3：手动触发**
1. 访问 GitHub Actions 页面
2. 选择 "Release Build" workflow
3. 点击 "Run workflow"

### 构建产物

| 平台 | 架构 | 产物 |
|------|------|------|
| Windows | x86_64 | Mem-Switch_x64.exe |
| Windows | ARM64 | Mem-Switch_ARM64.exe |
| Linux | x86_64 | Mem-Switch_amd64.AppImage, .deb |
| Linux | ARM64 | Mem-Switch_arm64.AppImage, .deb |
| macOS | x86_64 | Mem-Switch.app |
| macOS | ARM64 | Mem-Switch.app |
| macOS | Universal | Mem-Switch.app (x64+ARM64) |

---

## Windows 打包

### 方式一：cargo-xwin 交叉编译（exe 可执行文件）

使用 cargo-xwin 在 Linux 环境下交叉编译 Windows exe：

```bash
# 运行构建脚本
./scripts/build-windows-docker.sh

# 仅 x86_64
./scripts/build-windows-docker.sh --x64

# x86_64 + ARM64
./scripts/build-windows-docker.sh --all
```

**支持架构**:
- `x86_64-pc-windows-msvc` - Intel/AMD 64 位
- `aarch64-pc-windows-msvc` - ARM64

**输出位置**: `dist/windows/`

### 方式二：本地 Windows 环境（NSIS 安装包）

在 Windows 上直接构建，可生成 NSIS 安装包：

```bash
cd src-tauri

# x86_64 + NSIS
cargo tauri build --target x86_64-pc-windows-msvc --bundles nsis

# ARM64 + NSIS
cargo tauri build --target aarch64-pc-windows-msvc --bundles nsis
```

### 安装选项

Windows 安装包支持：
- ✅ 自定义安装位置（不默认 C 盘）
- ✅ 每用户/每机器安装模式
- ✅ 中文/英文语言选择
- ✅ 干净卸载（可选保留用户数据）

### Windows 架构说明

| 架构 | 目标设备 | 适用场景 |
|------|----------|----------|
| x86_64 | Intel/AMD 台式机和笔记本 | 大多数 Windows PC |
| ARM64 | Surface Pro X, Windows on ARM 笔记本 | 新一代 ARM Windows 设备 |

---

## Linux 打包

### 构建 AppImage 和 deb

```bash
# 运行构建脚本
./scripts/build-linux.sh
```

**输出位置**: `src-tauri/target/release/bundle/`
- `*.AppImage` - 便携式应用镜像
- `*.deb` - Debian/Ubuntu 安装包

### 多架构构建

```bash
# x86_64
cargo tauri build --target x86_64-unknown-linux-gnu

# ARM64
cargo tauri build --target aarch64-unknown-linux-gnu
```

### WSL/无桌面环境支持

Mem-Switch 包含智能启动脚本 `linux-launch.sh`，自动检测：
- Wayland 显示服务器
- X11 显示服务器
- WSLg (Windows Subsystem for Linux GUI)

**运行方式**:
```bash
# 直接运行（自动检测图形环境）
./src-tauri/linux-launch.sh

# 或手动指定
export DISPLAY=:0
./mem-switch
```

### WSLg 配置

Windows 11 + WSLg 用户：
1. 确保 Windows 已更新到最新版本
2. 运行 `wsl --shutdown` 重启 WSL
3. 重新启动 WSL 并运行应用

### VcXsrv 配置（旧版 WSL）

1. 在 Windows 上安装 VcXsrv
2. 运行 XLaunch，配置：
   - Multiple windows
   - Start no client
   - **Disable access control** (重要)
3. 在 WSL 中运行：
   ```bash
   export DISPLAY=:0
   ./mem-switch
   ```

### Linux 架构说明

| 架构 | 目标设备 | 适用场景 |
|------|----------|----------|
| x86_64 | Intel/AMD PC 和服务器 | 大多数 Linux 设备 |
| ARM64 | Raspberry Pi 4, Apple Silicon Mac (Linux), ARM 服务器 | 嵌入式设备, 新一代硬件 |

---

## macOS 打包

**注意**：macOS 构建需要 macOS 环境，无法在 Linux/Windows 交叉编译。

### 方式一：GitHub Actions（推荐）

推送版本标签自动触发构建：
```bash
git tag v0.1.0
git push origin v0.1.0
```

macOS 构建将在 GitHub Actions macOS runner 上自动执行，生成：
- x86_64 .app
- ARM64 .app
- Universal .app (x64 + ARM64 合并)

### 方式二：本地 macOS

在 macOS 设备上执行：
```bash
cd src-tauri

# Intel (x86_64)
cargo tauri build --target x86_64-apple-darwin

# Apple Silicon (ARM64)
cargo tauri build --target aarch64-apple-darwin

# 通用二进制（包含两种架构）
lipo -create \
  target/x86_64-apple-darwin/release/mem-switch-desktop \
  target/aarch64-apple-darwin/release/mem-switch-desktop \
  -output target/universal/mem-switch-desktop
```

**输出位置**: `src-tauri/target/release/bundle/`
- `*.app` - 应用程序包

### macOS 架构说明

| 架构 | 目标设备 | 适用场景 |
|------|----------|----------|
| x86_64 | Intel Mac | 旧款 Mac 设备 |
| ARM64 | Apple Silicon Mac (M1/M2/M3/M4) | 新款 Mac 设备 |
| Universal | 同时包含 x86_64 和 ARM64 | 在所有 Mac 上运行 |

---

## 安装包特性

### Windows (NSIS)
- 自定义安装位置
- 语言选择（中文/英文）
- 干净卸载
- 桌面/开始菜单快捷方式
- 多架构支持

### Linux (AppImage/deb)
- 无需 root 权限运行
- 自动检测图形环境
- WSL/WSLg 支持
- 依赖检查和提示
- 多架构支持

### macOS (app/dmg)
- 拖拽安装
- 签名和公证（需要开发者证书）
- 自动更新支持
- 通用二进制支持

---

## 故障排查

### Windows 安装失败
- 确保有管理员权限
- 关闭杀毒软件/Windows Defender 临时
- 检查磁盘空间
- 确认目标架构与 Windows 版本匹配

### Windows ARM 架构问题
- 确认 Windows on ARM 已启用开发者模式
- ARM64 应用在 x86_64 Windows 上通过模拟运行可能较慢

### Linux 启动失败
```bash
# 检查依赖
ldd mem-switch | grep "not found"

# 安装缺失依赖
sudo apt install libgtk-3-0 libwebkit2gtk-4.0-37 libappindicator3-1
```

### WSL 图形问题
```bash
# 检查 WSL 版本
wsl --list --verbose

# 更新 WSL
wsl --update

# 重启 WSL
wsl --shutdown
```

---

## 签名和公证

### Windows
需要代码签名证书：
```json
{
  "certificateThumbprint": "YOUR_THUMBPRINT",
  "timestampUrl": "http://timestamp.digicert.com"
}
```

### macOS
需要 Apple Developer 证书：
```bash
# 签名
codesign --sign "Developer ID Application: Your Name" mem-switch.app

# 公证
xcrun notarytool submit mem-switch.app --keychain-profile "your-profile"
```

---

## 版本发布检查清单

使用 GitHub Actions 自动构建：

1. [ ] 更新版本号：`src-tauri/tauri.conf.json` 中的 `version`
2. [ ] 更新版本号：`src-tauri/Cargo.toml` 中的 `version`
3. [ ] 本地测试确认无问题
4. [ ] 提交并推送更改
5. [ ] 创建版本标签：
   ```bash
   git tag v0.1.0 -m "Release v0.1.0"
   git push origin v0.1.0
   ```
6. [ ] 等待 GitHub Actions 完成构建
7. [ ] 检查 Release Draft 中的构建产物
8. [ ] 如需要，添加签名和公证（macOS）
9. [ ] 发布 GitHub Release

**自动构建产物**：
- Windows x86_64 exe
- Windows ARM64 exe
- Linux x86_64 AppImage + deb
- Linux ARM64 AppImage + deb (如果 Linux runner 支持)
- macOS Universal app

```bash
# 快速发布命令
./scripts/release.sh 0.1.0
```
          Mem-Switch_0.1.0_arm64.AppImage \
          > SHA256SUMS.txt
```
