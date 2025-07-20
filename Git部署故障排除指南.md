# Git部署故障排除指南

本指南帮助解决在部署OAuth回调处理页面到GitHub和Vercel时遇到的常见Git问题。

## 🚨 常见错误及解决方案

### 错误1：Repository not found

**错误信息**：
```bash
$ git push -u origin main
remote: Repository not found.
fatal: repository 'https://github.com/your-username/coze-oauth-handler.git/' not found
```

**原因分析**：
- GitHub仓库尚未创建
- 仓库名称不匹配
- 用户名错误
- 仓库访问权限问题

**解决方案**：

#### 方案1：创建GitHub仓库

1. **访问GitHub**：
   - 打开 [https://github.com](https://github.com)
   - 登录您的GitHub账号

2. **创建新仓库**：
   - 点击右上角的 "+" 按钮
   - 选择 "New repository"
   - 填写仓库信息：
     ```
     Repository name: coze-oauth-handler
     Description: OAuth callback handler for Coze.com integration
     Visibility: Public (推荐) 或 Private
     ```
   - **不要**勾选 "Add a README file"
   - 点击 "Create repository"

3. **获取正确的仓库URL**：
   创建后，GitHub会显示仓库URL，复制HTTPS链接：
   ```
   https://github.com/YOUR_ACTUAL_USERNAME/coze-oauth-handler.git
   ```

4. **更新本地远程仓库地址**：
   ```bash
   # 移除错误的远程地址
   git remote remove origin
   
   # 添加正确的远程地址（替换为您的实际用户名）
   git remote add origin https://github.com/YOUR_ACTUAL_USERNAME/coze-oauth-handler.git
   
   # 推送代码
   git push -u origin main
   ```

#### 方案2：检查用户名和仓库名

1. **确认GitHub用户名**：
   - 访问您的GitHub个人资料页面
   - URL中的用户名就是您的实际用户名
   - 例如：`https://github.com/actual-username`

2. **确认仓库名称**：
   - 检查您在GitHub上创建的仓库名称
   - 确保与本地配置的名称完全一致

3. **更新远程地址**：
   ```bash
   # 查看当前远程地址
   git remote -v
   
   # 更新为正确地址
   git remote set-url origin https://github.com/CORRECT_USERNAME/CORRECT_REPO_NAME.git
   ```

### 错误2：Authentication failed

**错误信息**：
```bash
remote: Support for password authentication was removed on August 13, 2021.
fatal: Authentication failed
```

**解决方案**：

#### 使用Personal Access Token

1. **创建Personal Access Token**：
   - 访问：[https://github.com/settings/tokens](https://github.com/settings/tokens)
   - 点击 "Generate new token" → "Generate new token (classic)"
   - 设置权限：
     - ☑️ `repo` - 完整仓库访问权限
     - ☑️ `workflow` - 工作流权限（如果需要）
   - 点击 "Generate token"
   - **立即复制并保存token**（只显示一次）

2. **使用Token进行认证**：
   ```bash
   # 方法1：在URL中包含token
   git remote set-url origin https://YOUR_TOKEN@github.com/username/repo.git
   
   # 方法2：使用Git凭据管理器
   git config --global credential.helper store
   git push -u origin main
   # 输入用户名：您的GitHub用户名
   # 输入密码：您的Personal Access Token
   ```

#### 使用SSH密钥（推荐）

1. **生成SSH密钥**：
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   ```

2. **添加SSH密钥到GitHub**：
   - 复制公钥内容：
     ```bash
     cat ~/.ssh/id_ed25519.pub
     ```
   - 访问：[https://github.com/settings/ssh](https://github.com/settings/ssh)
   - 点击 "New SSH key"
   - 粘贴公钥内容并保存

3. **使用SSH URL**：
   ```bash
   git remote set-url origin git@github.com:username/repo.git
   git push -u origin main
   ```

### 错误3：Branch 'main' not found

**错误信息**：
```bash
error: src refspec main does not match any
```

**解决方案**：

1. **检查当前分支**：
   ```bash
   git branch
   ```

2. **如果当前分支是master**：
   ```bash
   # 重命名分支为main
   git branch -M main
   git push -u origin main
   ```

3. **如果没有提交**：
   ```bash
   # 确保有文件被提交
   git add .
   git commit -m "Initial commit"
   git push -u origin main
   ```

## 🔧 完整部署流程（修正版）

### 步骤1：准备本地项目

```bash
# 1. 创建项目目录
mkdir coze-oauth-handler
cd coze-oauth-handler

# 2. 创建必要文件
# 创建 index.html, vercel.json 等文件（参考Vercel部署指南）

# 3. 初始化Git仓库
git init
git add .
git commit -m "Initial OAuth handler setup"
```

### 步骤2：创建GitHub仓库

1. 访问 [https://github.com/new](https://github.com/new)
2. 创建名为 `coze-oauth-handler` 的仓库
3. 选择 Public 可见性
4. **不要**添加README、.gitignore或license
5. 点击 "Create repository"

### 步骤3：连接并推送

```bash
# 1. 添加远程仓库（替换为您的实际用户名）
git remote add origin https://github.com/YOUR_USERNAME/coze-oauth-handler.git

# 2. 设置主分支
git branch -M main

# 3. 推送代码
git push -u origin main
```

### 步骤4：部署到Vercel

1. 访问 [https://vercel.com](https://vercel.com)
2. 使用GitHub账号登录
3. 点击 "New Project"
4. 选择刚才创建的 `coze-oauth-handler` 仓库
5. 点击 "Deploy"
6. 等待部署完成

## 🛠️ 实用Git命令

### 查看状态和配置

```bash
# 查看Git状态
git status

# 查看远程仓库
git remote -v

# 查看分支
git branch -a

# 查看提交历史
git log --oneline
```

### 修复常见问题

```bash
# 重置远程仓库地址
git remote remove origin
git remote add origin https://github.com/username/repo.git

# 强制推送（谨慎使用）
git push -f origin main

# 拉取远程更新
git pull origin main

# 重置到上一次提交
git reset --hard HEAD~1
```

## 📋 部署检查清单

完成部署前，请确认：

**本地准备**：
- ☐ 项目文件已创建（index.html, vercel.json等）
- ☐ Git仓库已初始化
- ☐ 文件已添加并提交
- ☐ 分支名为 `main`

**GitHub仓库**：
- ☐ GitHub仓库已创建
- ☐ 仓库名称正确
- ☐ 用户名正确
- ☐ 仓库可见性设置合适

**认证配置**：
- ☐ Personal Access Token已创建（如使用HTTPS）
- ☐ SSH密钥已配置（如使用SSH）
- ☐ Git凭据已保存

**推送验证**：
- ☐ 远程仓库地址正确
- ☐ 代码成功推送到GitHub
- ☐ GitHub仓库中可以看到文件

**Vercel部署**：
- ☐ Vercel项目已创建
- ☐ 部署成功完成
- ☐ 部署URL可正常访问
- ☐ OAuth回调页面正常显示

## 🆘 获取帮助

如果仍然遇到问题：

1. **检查GitHub状态**：[https://www.githubstatus.com](https://www.githubstatus.com)
2. **查看Git文档**：[https://git-scm.com/docs](https://git-scm.com/docs)
3. **Vercel文档**：[https://vercel.com/docs](https://vercel.com/docs)
4. **联系支持**：
   - GitHub Support: [https://support.github.com](https://support.github.com)
   - Vercel Support: [https://vercel.com/help](https://vercel.com/help)

---

**💡 提示**：建议先在GitHub上创建仓库，然后再进行本地Git配置，这样可以避免大部分认证和仓库不存在的问题。