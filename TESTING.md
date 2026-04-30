# Mem-Switch 测试指南

## 测试环境

**本地开发环境**（功能验证 + Bug 修复）：
- **前端**: http://localhost:5173
- **后端**: http://localhost:8000
- **版本**: 开发中（main 分支）

**构建产物**：由 GitHub Actions 自动构建，访问 Release 页面下载

---

## 本地功能测试清单

### 基础功能
- [ ] 后端服务启动正常
- [ ] 前端页面加载正常
- [ ] 健康检查 API 正常：`/api/health`

### Onboarding 首次启动
- [ ] 显示欢迎界面
- [ ] Ollama 配置可测试连接
- [ ] 模型选择步骤正常
- [ ] 可跳过或执行数据导入
- [ ] 完成后进入主界面

### 批量导入
- [ ] 可选择多个文件
- [ ] 显示文件列表
- [ ] 进度条显示正确
- [ ] 已导入会话自动跳过
- [ ] 完成显示统计

### 记忆管理
- [ ] 记忆列表显示正常
- [ ] 编辑功能正常
- [ ] 失效/恢复功能正常
- [ ] 删除功能正常
- [ ] 统计信息显示（调用次数）

### 统一搜索
- [ ] 搜索面板正常显示
- [ ] 多范围搜索正常
- [ ] 搜索结果正确
- [ ] 缓存生效（第二次搜索更快）

### 错误处理
- [ ] Toast 通知正常显示
- [ ] 成功/错误/警告样式正确
- [ ] 通知自动消失

---

## 本地测试命令

```bash
# 1. 启动后端
cd backend
uv run uvicorn main:app --port 8000

# 2. 启动前端（新终端）
cd frontend
npm run dev

# 3. 测试 API
curl http://localhost:8000/api/health
curl http://localhost:8000/api/settings
curl http://localhost:8000/api/memory/list

# 4. 前端构建测试
cd frontend && npm run build
```

---

## GitHub Actions 测试

### 自动触发条件
- Push 到 main 分支
- Pull Request 到 main 分支
- 推送版本标签 (`v*`)

### CI 检查项
1. **Backend Tests**: pytest 运行
2. **Frontend Build**: Vite 构建
3. **Rust Check**: cargo check
4. **API Integration**: 健康检查 + 端点测试

### 查看 CI 状态
访问：https://github.com/1234567mm/mem-switch/actions

---

## 发布测试

### 1. 创建版本标签
```bash
git tag v0.1.0
git push origin v0.1.0
```

### 2. 等待 GitHub Actions
- Linux 构建 (~10 分钟)
- Windows 构建 (~15 分钟)
- macOS 构建 (~20 分钟)

### 3. 检查 Release Draft
1. 访问 https://github.com/1234567mm/mem-switch/releases
2. 查看 "Draft"状态的 Release
3. 检查所有平台的构建产物
4. 添加发布说明
5. 点击 "Publish release"

---

## 反馈收集

### 测试后填写

**最喜欢的新功能**: _______________

**最困惑的地方**: _______________

**建议改进**: _______________

**发现的问题**: _______________

---

## 版本发布检查清单

- [ ] 所有本地功能测试通过
- [ ] CI 所有检查通过
- [ ] 代码合并到 main
- [ ] 创建版本标签
- [ ] GitHub Actions 构建完成
- [ ] Release Draft 检查
- [ ] 发布说明填写完整
- [ ] 正式发布
