# Vercel部署故障排除指南

当您的Vercel部署出现404、401或其他错误时，请按照以下步骤进行排查和修复。

## 🚨 常见错误类型

### 1. 404 Not Found 错误
**症状**：访问部署URL时显示"404: 未找到"

**可能原因**：
- 文件结构不正确
- `vercel.json` 配置错误
- 路由重写规则问题
- 部署失败但显示成功

### 2. 401 Unauthorized 错误
**症状**：访问时显示认证错误

**可能原因**：
- 项目设置为私有
- 域名配置问题
- Vercel账户权限问题

### 3. 500 Internal Server Error
**症状**：服务器内部错误

**可能原因**：
- 代码语法错误
- 依赖项缺失
- 环境变量配置错误

## 🔧 立即修复方案

### 步骤1：检查部署状态

1. **登录Vercel控制台**：
   - 访问 [https://vercel.com/dashboard](https://vercel.com/dashboard)
   - 找到您的 `coze-oauth-handler` 项目

2. **查看部署详情**：
   - 点击项目名称
   - 查看最新部署的状态
   - 检查是否有错误日志

### 步骤2：验证文件结构

确保您的项目文件结构如下：

```
coze-oauth-handler/
├── index.html          # 主页面
├── vercel.json         # Vercel配置
├── api/                # API路由（可选）
│   └── oauth/
│       └── callback.js
└── README.md           # 说明文档（可选）
```

### 步骤3：修复配置文件

#### 更新 `vercel.json`

```json
{
  "rewrites": [
    {
      "source": "/oauth/callback",
      "destination": "/index.html"
    },
    {
      "source": "/",
      "destination": "/index.html"
    }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "Cache-Control",
          "value": "public, max-age=0, must-revalidate"
        }
      ]
    }
  ]
}
```

#### 简化的 `index.html`（确保基本功能）

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OAuth授权处理</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        .success { color: #28a745; }
        .error { color: #dc3545; }
        .code {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            font-family: monospace;
            word-break: break-all;
            margin: 20px 0;
            border: 1px solid #dee2e6;
        }
        .copy-btn {
            background: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin-top: 10px;
        }
        .copy-btn:hover {
            background: #0056b3;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 OAuth授权处理</h1>
        <div id="status">正在处理授权...</div>
        <div id="result"></div>
        
        <!-- 调试信息 -->
        <div id="debug" style="margin-top: 30px; padding: 15px; background: #f8f9fa; border-radius: 5px; font-size: 12px; text-align: left;">
            <strong>调试信息：</strong><br>
            <span id="debug-info"></span>
        </div>
    </div>

    <script>
        function getUrlParams() {
            const params = new URLSearchParams(window.location.search);
            return {
                code: params.get('code'),
                state: params.get('state'),
                error: params.get('error'),
                error_description: params.get('error_description')
            };
        }

        function copyToClipboard(text) {
            if (navigator.clipboard) {
                navigator.clipboard.writeText(text).then(() => {
                    alert('授权码已复制到剪贴板！');
                }).catch(() => {
                    fallbackCopy(text);
                });
            } else {
                fallbackCopy(text);
            }
        }

        function fallbackCopy(text) {
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            try {
                document.execCommand('copy');
                alert('授权码已复制到剪贴板！');
            } catch (err) {
                alert('复制失败，请手动复制授权码');
            }
            document.body.removeChild(textArea);
        }

        function handleOAuthCallback() {
            const params = getUrlParams();
            const statusDiv = document.getElementById('status');
            const resultDiv = document.getElementById('result');
            const debugDiv = document.getElementById('debug-info');

            // 显示调试信息
            debugDiv.innerHTML = `
                URL: ${window.location.href}<br>
                Code: ${params.code || '无'}<br>
                State: ${params.state || '无'}<br>
                Error: ${params.error || '无'}<br>
                Error Description: ${params.error_description || '无'}<br>
                Timestamp: ${new Date().toLocaleString()}
            `;

            if (params.error) {
                statusDiv.innerHTML = '<div class="error">❌ 授权失败</div>';
                resultDiv.innerHTML = `
                    <p><strong>错误类型：</strong>${params.error}</p>
                    <p><strong>错误描述：</strong>${params.error_description || '未知错误'}</p>
                    <p>请返回应用重新尝试授权。</p>
                `;
            } else if (params.code) {
                statusDiv.innerHTML = '<div class="success">✅ 授权成功</div>';
                resultDiv.innerHTML = `
                    <p>授权码已获取，请复制以下代码：</p>
                    <div class="code" id="authCode">${params.code}</div>
                    <button class="copy-btn" onclick="copyToClipboard('${params.code}')">复制授权码</button>
                    <p style="margin-top: 20px; font-size: 14px; color: #666;">
                        请将此授权码粘贴到您的应用中完成OAuth流程。<br>
                        授权码有效期通常为10分钟，请尽快使用。
                    </p>
                `;
            } else {
                statusDiv.innerHTML = '<div class="success">✅ 页面加载成功</div>';
                resultDiv.innerHTML = `
                    <p>OAuth回调处理页面已就绪。</p>
                    <p>此页面用于处理来自coze.com的OAuth授权回调。</p>
                    <p style="font-size: 14px; color: #666; margin-top: 20px;">
                        如果您看到此页面，说明部署成功！<br>
                        回调URL: <code>${window.location.origin}/oauth/callback</code>
                    </p>
                `;
            }
        }

        // 页面加载完成后处理回调
        document.addEventListener('DOMContentLoaded', handleOAuthCallback);
    </script>
</body>
</html>
```

### 步骤4：重新部署

#### 方法1：通过Git推送

```bash
# 确保在项目目录中
cd coze-oauth-handler

# 添加修改的文件
git add .
git commit -m "Fix deployment configuration"
git push origin main
```

#### 方法2：通过Vercel CLI

```bash
# 安装Vercel CLI
npm i -g vercel

# 登录Vercel
vercel login

# 部署项目
vercel --prod
```

#### 方法3：手动重新部署

1. 在Vercel控制台中找到您的项目
2. 点击 "Deployments" 标签
3. 点击最新部署旁边的 "..." 菜单
4. 选择 "Redeploy"

### 步骤5：验证修复

1. **测试基本访问**：
   ```
   https://coze-oauth-handler-cbe7frlwb-feigs0710s-projects.vercel.app
   ```
   应该显示OAuth处理页面

2. **测试回调路径**：
   ```
   https://coze-oauth-handler-cbe7frlwb-feigs0710s-projects.vercel.app/oauth/callback
   ```
   应该显示相同的页面

3. **测试带参数的回调**：
   ```
   https://coze-oauth-handler-cbe7frlwb-feigs0710s-projects.vercel.app/oauth/callback?code=test123&state=test
   ```
   应该显示成功处理授权码的页面

## 🔍 高级故障排除

### 查看部署日志

1. 在Vercel项目页面，点击 "Functions" 标签
2. 查看实时日志和错误信息
3. 检查构建日志中的错误

### 检查域名配置

1. 确认项目设置中的域名配置
2. 检查DNS设置（如果使用自定义域名）
3. 验证SSL证书状态

### 环境变量检查

1. 在项目设置中检查环境变量
2. 确保没有敏感信息暴露
3. 验证变量名称和值的正确性

## 🆘 紧急备用方案

如果上述方法都无法解决问题，可以使用以下备用方案：

### 方案1：使用GitHub Pages

```bash
# 在GitHub仓库设置中启用Pages
# 选择main分支作为源
# 您的URL将是：https://username.github.io/coze-oauth-handler
```

### 方案2：使用Netlify

1. 访问 [https://netlify.com](https://netlify.com)
2. 连接您的GitHub仓库
3. 部署项目

### 方案3：本地测试服务器

```bash
# 使用Python启动本地服务器
python -m http.server 8000

# 或使用Node.js
npx serve .

# 然后使用ngrok暴露到公网
ngrok http 8000
```

## 📞 获取帮助

如果问题仍然存在：

1. **检查Vercel状态页面**：[https://vercel-status.com](https://vercel-status.com)
2. **查看Vercel文档**：[https://vercel.com/docs](https://vercel.com/docs)
3. **联系Vercel支持**：通过控制台提交支持票据

## ✅ 成功部署检查清单

- [ ] 文件结构正确
- [ ] `vercel.json` 配置无误
- [ ] `index.html` 语法正确
- [ ] Git推送成功
- [ ] Vercel部署无错误
- [ ] 基本URL可访问
- [ ] 回调URL可访问
- [ ] 参数处理正常
- [ ] 复制功能工作
- [ ] 调试信息显示

---

**提示**：保存此故障排除指南，在遇到部署问题时可以快速参考解决方案。