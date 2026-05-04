# GitHub Actions 打包失败修复计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 GitHub Actions workflow 中的 Rust action 引用错误，使自动打包正常工作

**Architecture:** 修正三个 workflow 文件中错误的 `dtolnay/rust-action` 引用为正确的 `dtolnay/rust`

**Tech Stack:** GitHub Actions, Rust

---

## 问题分析

**错误日志：**
```
Unable to resolve action dtolnay/rust-action, repository not found
```

**根因：** 所有 workflow 文件使用了不存在的 action `dtolnay/rust-action@stable`，正确名称是 `dtolnay/rust@stable`

**受影响文件：**
- `.github/workflows/ci.yml` - 第 100 行
- `.github/workflows/release.yml` - 第 28, 92, 156 行
- `.github/workflows/nightly-build.yml` - 第 39, 105, 171 行

---

## 任务 1: 修复 ci.yml 中的 Rust action 引用

**Files:**
- Modify: `.github/workflows/ci.yml:100`

- [ ] **Step 1: 修复 ci.yml 中的 rust-action 引用**

```yaml
# 修改前（第 100 行）
        uses: dtolnay/rust-action@stable

# 修改后
        uses: dtolnay/rust@stable
```

- [ ] **Step 2: 验证修改**

```bash
grep -n "dtolnay/rust" .github/workflows/ci.yml
```

预期输出：`uses: dtolnay/rust@stable` (不再有 rust-action)

- [ ] **Step 3: 提交更改**

```bash
git add .github/workflows/ci.yml
git commit -m "fix: correct rust-action to rust in CI workflow"
```

---

## 任务 2: 修复 release.yml 中的 Rust action 引用

**Files:**
- Modify: `.github/workflows/release.yml:28`
- Modify: `.github/workflows/release.yml:92`
- Modify: `.github/workflows/release.yml:156`

- [ ] **Step 1: 修复 release.yml 中的三处 rust-action 引用**

使用 `replace_all` 将所有 `dtolnay/rust-action` 替换为 `dtolnay/rust`：

```bash
sed -i 's/dtolnay\/rust-action/dtolnay\/rust/g' .github/workflows/release.yml
```

- [ ] **Step 2: 验证修改**

```bash
grep -n "dtolnay/rust" .github/workflows/release.yml
```

预期输出：三处都是 `uses: dtolnay/rust@stable`

- [ ] **Step 3: 提交更改**

```bash
git add .github/workflows/release.yml
git commit -m "fix: correct rust-action to rust in release workflow"
```

---

## 任务 3: 修复 nightly-build.yml 中的 Rust action 引用

**Files:**
- Modify: `.github/workflows/nightly-build.yml:39`
- Modify: `.github/workflows/nightly-build.yml:105`
- Modify: `.github/workflows/nightly-build.yml:171`

- [ ] **Step 1: 修复 nightly-build.yml 中的三处 rust-action 引用**

```bash
sed -i 's/dtolnay\/rust-action/dtolnay\/rust/g' .github/workflows/nightly-build.yml
```

- [ ] **Step 2: 验证修改**

```bash
grep -n "dtolnay/rust" .github/workflows/nightly-build.yml
```

预期输出：三处都是 `uses: dtolnay/rust@stable`

- [ ] **Step 3: 提交更改**

```bash
git add .github/workflows/nightly-build.yml
git commit -m "fix: correct rust-action to rust in nightly build workflow"
```

---

## 任务 4: 验证修复并推送

- [ ] **Step 1: 确认没有遗漏的 rust-action 引用**

```bash
grep -rn "dtolnay/rust-action" .github/workflows/
```

预期输出：无输出（找不到任何匹配）

- [ ] **Step 2: 推送修复**

```bash
git push origin main
```

- [ ] **Step 3: 创建测试标签验证 workflow**

```bash
git tag v0.1.1-test
git push origin v0.1.1-test
```

- [ ] **Step 4: 监控 GitHub Actions 运行**

访问：`https://github.com/1234567mm/mem-switch/actions`

预期：Release Build workflow 应该成功运行

- [ ] **Step 5: 删除测试标签**

```bash
git tag -d v0.1.1-test
git push origin :refs/tags/v0.1.1-test
```

---

## 验证清单

- [ ] `ci.yml` 中所有 `dtolnay/rust-action` 已改为 `dtolnay/rust`
- [ ] `release.yml` 中所有 `dtolnay/rust-action` 已改为 `dtolnay/rust`
- [ ] `nightly-build.yml` 中所有 `dtolnay/rust-action` 已改为 `dtolnay/rust`
- [ ] 没有遗漏的 `rust-action` 引用
- [ ] 更改已推送到 GitHub
- [ ] GitHub Actions 成功执行（推送标签测试）

---

## 回滚计划（如果需要）

如果修复后仍有问题，可以使用以下命令回滚：

```bash
git revert HEAD~1  # 回滚最后一次提交
git push origin main
```