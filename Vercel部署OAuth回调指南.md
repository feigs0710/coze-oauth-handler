# Vercel部署OAuth回调处理指南

本指南将帮助您在Vercel上部署OAuth回调处理页面，用于处理来自coze.com的OAuth授权回调。

## 前提条件

- GitHub账号
- Vercel账号（可以使用GitHub登录）
- 基本的Git操作知识

## 方案一：使用我们提供的模板（推荐）

### 步骤1：创建项目文件

在您的本地创建一个新文件夹，例如 `coze-oauth-handler`，然后创建以下文件：

#### 1. 创建 `index.html`

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OAuth授权处理</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
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
        .success {
            color: #28a745;
            font-size: 18px;
            margin-bottom: 20px;
        }
        .error {
            color: #dc3545;
            font-size: 18px;
            margin-bottom: 20px;
        }
        .code {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            font-family: monospace;
            word-break: break-all;
            margin: 20px 0;
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
            navigator.clipboard.writeText(text).then(() => {
                alert('授权码已复制到剪贴板！');
            }).catch(() => {
                alert('复制失败，请手动复制授权码');
            });
        }

        function handleOAuthCallback() {
            const params = getUrlParams();
            const statusDiv = document.getElementById('status');
            const resultDiv = document.getElementById('result');

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
                statusDiv.innerHTML = '<div class="error">❌ 未检测到有效的授权参数</div>';
                resultDiv.innerHTML = '<p>请确保从正确的OAuth授权链接访问此页面。</p>';
            }
        }

        // 页面加载完成后处理回调
        document.addEventListener('DOMContentLoaded', handleOAuthCallback);
    </script>
</body>
</html>
```

#### 2. 创建 `api/oauth/callback.js`（可选，用于服务端处理）

```javascript
export default function handler(req, res) {
    // 设置CORS头
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        res.status(200).end();
        return;
    }

    const { code, state, error, error_description } = req.query;

    if (error) {
        res.status(400).json({
            success: false,
            error: error,
            error_description: error_description
        });
        return;
    }

    if (code) {
        res.status(200).json({
            success: true,
            code: code,
            state: state,
            message: 'Authorization code received successfully'
        });
        return;
    }

    res.status(400).json({
        success: false,
        error: 'invalid_request',
        error_description: 'No authorization code or error received'
    });
}
```

#### 3. 创建 `vercel.json`

```json
{
  "rewrites": [
    {
      "source": "/oauth/callback",
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
        }
      ]
    }
  ]
}
```

### 步骤2：推送到GitHub

1. 在GitHub上创建新仓库，例如 `coze-oauth-handler`
2. 将本地文件推送到GitHub：

```bash
git init
git add .
git commit -m "Initial OAuth handler setup"
git branch -M main
git remote add origin https://github.com/your-username/coze-oauth-handler.git
git push -u origin main
```

### 步骤3：部署到Vercel

1. 访问 [https://vercel.com](https://vercel.com)
2. 使用GitHub账号登录
3. 点击 "New Project"
4. 选择您刚才创建的 `coze-oauth-handler` 仓库
5. 点击 "Deploy"
6. 等待部署完成

### 步骤4：获取部署URL

部署完成后，Vercel会提供一个URL，格式类似：
```
https://coze-oauth-handler-xxx.vercel.app
```

您的OAuth回调URL将是：
```
https://coze-oauth-handler-xxx.vercel.app/oauth/callback
```

## 方案二：一键部署（最简单）

点击下面的按钮一键部署到Vercel：

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/your-template-repo/coze-oauth-handler)

## 测试部署

### 1. 测试基本访问

访问您的部署URL：
```
https://your-app.vercel.app
```

应该看到OAuth处理页面。

### 2. 测试回调处理

访问带参数的回调URL：
```
https://your-app.vercel.app/oauth/callback?code=test_code&state=test_state
```

应该看到成功处理授权码的页面。

## 自定义域名（可选）

如果您有自己的域名，可以在Vercel中配置：

1. 在Vercel项目设置中找到 "Domains"
2. 添加您的自定义域名
3. 按照提示配置DNS记录
4. 等待SSL证书自动配置完成

## 安全注意事项

1. **HTTPS强制**：Vercel自动提供HTTPS，确保所有OAuth流程都通过安全连接
2. **域名验证**：在coze.com中配置重定向URI时，确保域名完全匹配
3. **状态参数**：建议在OAuth流程中使用state参数防止CSRF攻击
4. **授权码处理**：授权码应该立即使用，不要长期存储

## 常见问题

### Q: 部署后访问404错误？
A: 检查 `vercel.json` 配置是否正确，确保重写规则指向正确的文件。

### Q: OAuth回调失败？
A: 
1. 确认重定向URI在coze.com中配置正确
2. 检查URL是否完全匹配（包括协议、域名、路径）
3. 确认部署成功且页面可访问

### Q: 如何查看部署日志？
A: 在Vercel项目页面的 "Functions" 标签中可以查看详细日志。

### Q: 可以使用免费版本吗？
A: 是的，Vercel的免费版本完全足够处理OAuth回调需求。

## 下一步

部署完成后：

1. 复制您的回调URL
2. 在coze.com的OAuth应用配置中填入此URL
3. 使用 `oauth_test_tool.py` 测试完整的OAuth流程
4. 集成到您的coze.cn插件中

---

**提示**：保存好您的Vercel部署URL，这将是您在coze.com中配置OAuth重定向URI时需要使用的地址。