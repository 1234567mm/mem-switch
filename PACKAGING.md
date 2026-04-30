# Mem-Switch 打包指南

## Windows 打包

### 方式一：Docker 跨平台构建（推荐）

在 Linux 环境下使用 Docker 构建 Windows 安装包：

```bash
# 运行构建脚本
./scripts/build-windows-docker.sh
```

**输出位置**: `dist/windows/`

### 方式二：本地 Windows 环境

```bash
cd src-tauri
cargo tauri build --target x86_64-pc-windows-msvc
```

### 安装选项

Windows 安装包支持：
- ✅ 自定义安装位置（不默认 C 盘）
- ✅ 每用户/每机器安装模式
- ✅ 中文/英文语言选择
- ✅ 干净卸载（可选保留用户数据）

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

---

## macOS 打包

```bash
cd src-tauri
cargo tauri build --target x86_64-apple-darwin
cargo tauri build --target aarch64-apple-darwin
```

**输出位置**: `src-tauri/target/release/bundle/`
- `*.app` - 应用程序包
- `*.dmg` - 磁盘镜像安装包

---

## 安装包特性

### Windows (NSIS)
- 自定义安装位置
- 语言选择（中文/英文）
- 干净卸载
- 桌面/开始菜单快捷方式

### Linux (AppImage/deb)
- 无需 root 权限运行
- 自动检测图形环境
- WSL/WSLg 支持
- 依赖检查和提示

### macOS (app/dmg)
- 拖拽安装
- 签名和公证（需要开发者证书）
- 自动更新支持

---

## 故障排查

### Windows 安装失败
- 确保有管理员权限
- 关闭杀毒软件/Windows Defender 临时
- 检查磁盘空间

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

## 版本发布

1. 更新版本号：`src-tauri/tauri.conf.json`
2. 构建所有平台
3. 生成 SHA256 校验和
4. 创建 GitHub Release
5. 上传安装包

```bash
# 生成校验和
sha256sum Mem-Switch*.exe Mem-Switch*.AppImage Mem-Switch*.deb > SHA256SUMS.txt
```
