# Git配置优化指南

本指南提供了Git配置的最佳实践和常见问题解决方案，帮助您更好地管理代码版本控制。

## 🚨 当前问题解决

### 问题分析
根据您的终端输出，遇到了以下问题：
1. `remote origin already exists` - 远程仓库已存在
2. `Repository not found` - 仓库未找到
3. 远程URL指向了错误的仓库

### 立即解决方案

```bash
# 1. 查看当前远程仓库配置
git remote -v

# 2. 删除现有的origin远程仓库
git remote remove origin

# 3. 添加正确的远程仓库
git remote add origin https://github.com/feigs0710/coze-oauth-handler.git

# 4. 验证远程仓库配置
git remote -v

# 5. 推送到远程仓库
git push -u origin main
```

## 🔧 Git配置优化

### 1. 全局配置设置

```bash
# 设置用户信息
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# 设置默认分支名
git config --global init.defaultBranch main

# 设置换行符处理（Windows推荐）
git config --global core.autocrlf true

# 设置编辑器
git config --global core.editor "code --wait"  # VS Code
# 或者
git config --global core.editor "notepad"     # 记事本

# 启用颜色输出
git config --global color.ui auto

# 设置推送策略
git config --global push.default simple
```

### 2. 项目级配置

```bash
# 在项目根目录下执行
cd /path/to/your/project

# 设置项目特定的用户信息（如果需要）
git config user.name "Project Specific Name"
git config user.email "project@example.com"

# 设置上游分支跟踪
git config branch.main.remote origin
git config branch.main.merge refs/heads/main
```

### 3. .gitconfig 示例配置

创建或编辑 `~/.gitconfig` 文件：

```ini
[user]
    name = Your Name
    email = your.email@example.com

[core]
    editor = code --wait
    autocrlf = true
    filemode = false

[init]
    defaultBranch = main

[push]
    default = simple
    autoSetupRemote = true

[pull]
    rebase = false

[color]
    ui = auto

[alias]
    st = status
    co = checkout
    br = branch
    ci = commit
    lg = log --oneline --graph --decorate --all
    last = log -1 HEAD
    unstage = reset HEAD --
    visual = !gitk

[credential]
    helper = manager-core

[diff]
    tool = vscode

[difftool "vscode"]
    cmd = code --wait --diff $LOCAL $REMOTE

[merge]
    tool = vscode

[mergetool "vscode"]
    cmd = code --wait $MERGED
```

## 📁 .gitignore 优化

### Python项目 .gitignore

```gitignore
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
cover/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
.pybuilder/
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
.python-version

# pipenv
Pipfile.lock

# poetry
poetry.lock

# pdm
.pdm.toml

# PEP 582
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# pytype static type analyzer
.pytype/

# Cython debug symbols
cython_debug/

# PyCharm
.idea/

# VS Code
.vscode/
!.vscode/settings.json
!.vscode/tasks.json
!.vscode/launch.json
!.vscode/extensions.json
*.code-workspace

# Local History for Visual Studio Code
.history/

# Built Visual Studio Code Extensions
*.vsix

# 项目特定文件
config.json
secrets.json
*.key
*.pem
*.p12
*.pfx

# 日志文件
*.log
logs/

# 临时文件
*.tmp
*.temp
*.swp
*.swo
*~

# 操作系统文件
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
desktop.ini

# 备份文件
*.bak
*.backup
*.old
```

## 🌿 分支管理策略

### Git Flow 工作流

```bash
# 1. 主分支
main        # 生产环境代码
develop     # 开发环境代码

# 2. 功能分支
feature/oauth-integration
feature/error-handling
feature/performance-optimization

# 3. 发布分支
release/v1.0.0
release/v1.1.0

# 4. 热修复分支
hotfix/critical-bug-fix
```

### 分支操作命令

```bash
# 创建并切换到新分支
git checkout -b feature/new-feature

# 切换分支
git checkout main
git checkout develop

# 合并分支
git checkout main
git merge feature/new-feature

# 删除分支
git branch -d feature/new-feature  # 本地删除
git push origin --delete feature/new-feature  # 远程删除

# 查看所有分支
git branch -a
```

## 📝 提交信息规范

### Conventional Commits 格式

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### 提交类型

- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式化（不影响功能）
- `refactor`: 代码重构
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动
- `ci`: CI/CD相关
- `build`: 构建系统或外部依赖的变动

### 提交示例

```bash
# 好的提交信息
git commit -m "feat(oauth): add token refresh mechanism"
git commit -m "fix(api): handle network timeout errors"
git commit -m "docs(readme): update installation instructions"
git commit -m "refactor(auth): simplify authentication flow"

# 多行提交信息
git commit -m "feat(oauth): add automatic token refresh

- Implement token expiration detection
- Add background refresh mechanism
- Update error handling for expired tokens

Closes #123"
```

## 🔄 常用Git工作流

### 日常开发流程

```bash
# 1. 更新本地代码
git checkout main
git pull origin main

# 2. 创建功能分支
git checkout -b feature/new-feature

# 3. 开发和提交
git add .
git commit -m "feat: implement new feature"

# 4. 推送分支
git push -u origin feature/new-feature

# 5. 创建Pull Request（在GitHub上）

# 6. 合并后清理
git checkout main
git pull origin main
git branch -d feature/new-feature
```

### 紧急修复流程

```bash
# 1. 从main创建hotfix分支
git checkout main
git pull origin main
git checkout -b hotfix/critical-fix

# 2. 修复问题
git add .
git commit -m "fix: resolve critical security issue"

# 3. 推送并合并
git push -u origin hotfix/critical-fix
# 创建PR并立即合并

# 4. 同步到develop分支
git checkout develop
git pull origin develop
git merge main
git push origin develop
```

## 🛠️ Git工具和扩展

### 推荐的Git工具

1. **Git GUI工具**：
   - GitHub Desktop
   - SourceTree
   - GitKraken
   - VS Code Git扩展

2. **命令行增强**：
   - Oh My Zsh (with git plugin)
   - Git Bash (Windows)
   - PowerShell Git模块

3. **Git Hooks**：
   - pre-commit hooks
   - commit-msg hooks
   - pre-push hooks

### Pre-commit Hook 示例

创建 `.git/hooks/pre-commit` 文件：

```bash
#!/bin/sh
# Pre-commit hook script

# 运行代码格式检查
echo "Running code quality checks..."

# Python代码检查
if command -v flake8 >/dev/null 2>&1; then
    echo "Running flake8..."
    flake8 .
    if [ $? -ne 0 ]; then
        echo "flake8 failed. Please fix the issues before committing."
        exit 1
    fi
fi

# 运行测试
if command -v pytest >/dev/null 2>&1; then
    echo "Running tests..."
    pytest --tb=short
    if [ $? -ne 0 ]; then
        echo "Tests failed. Please fix the issues before committing."
        exit 1
    fi
fi

echo "All checks passed!"
exit 0
```

## 🚨 故障排除

### 常见问题和解决方案

#### 1. 远程仓库问题

```bash
# 问题：remote origin already exists
# 解决：
git remote remove origin
git remote add origin <new-url>

# 问题：Repository not found
# 解决：检查仓库URL和权限
git remote set-url origin <correct-url>
```

#### 2. 合并冲突

```bash
# 查看冲突文件
git status

# 手动解决冲突后
git add <resolved-files>
git commit -m "resolve merge conflicts"
```

#### 3. 撤销操作

```bash
# 撤销最后一次提交（保留更改）
git reset --soft HEAD~1

# 撤销最后一次提交（丢弃更改）
git reset --hard HEAD~1

# 撤销文件更改
git checkout -- <file>

# 撤销暂存
git reset HEAD <file>
```

#### 4. 换行符问题

```bash
# Windows系统推荐设置
git config --global core.autocrlf true

# 如果已经出现警告，可以忽略或修复
git config --global core.safecrlf false
```

## 📊 Git性能优化

### 大型仓库优化

```bash
# 启用文件系统监控
git config core.fsmonitor true

# 启用部分克隆
git clone --filter=blob:none <url>

# 浅克隆
git clone --depth 1 <url>

# 垃圾回收
git gc --aggressive

# 清理未跟踪文件
git clean -fd
```

### 仓库维护

```bash
# 检查仓库完整性
git fsck

# 优化仓库
git repack -ad

# 清理引用日志
git reflog expire --expire=now --all
git gc --prune=now
```

## 🔐 安全最佳实践

### 1. 敏感信息保护

```bash
# 永远不要提交敏感信息
# 使用 .gitignore 排除敏感文件
echo "*.key" >> .gitignore
echo "*.pem" >> .gitignore
echo "config.json" >> .gitignore
echo ".env" >> .gitignore

# 如果已经提交了敏感信息，使用 git-filter-repo 清理
pip install git-filter-repo
git filter-repo --path config.json --invert-paths
```

### 2. 签名提交

```bash
# 生成GPG密钥
gpg --gen-key

# 配置Git使用GPG签名
git config --global user.signingkey <key-id>
git config --global commit.gpgsign true

# 签名提交
git commit -S -m "signed commit"
```

### 3. 访问控制

```bash
# 使用SSH密钥而不是密码
ssh-keygen -t ed25519 -C "your_email@example.com"

# 添加SSH密钥到ssh-agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# 测试SSH连接
ssh -T git@github.com
```

## 📈 监控和分析

### Git统计信息

```bash
# 查看提交统计
git log --oneline --graph --decorate --all
git log --stat
git log --author="Your Name" --since="2023-01-01"

# 查看文件变更历史
git log --follow -- <file>

# 查看代码贡献统计
git shortlog -sn

# 查看仓库大小
git count-objects -vH
```

### 分支分析

```bash
# 查看分支关系
git show-branch --all

# 查看未合并的分支
git branch --no-merged
git branch --merged

# 查看分支最后提交时间
git for-each-ref --format='%(refname:short) %(committerdate)' refs/heads
```

---

通过遵循这些Git配置和最佳实践，您可以建立一个高效、安全、可维护的版本控制工作流程。记住定期备份重要代码，并保持良好的提交习惯。