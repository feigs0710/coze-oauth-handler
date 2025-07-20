# Coze.com OAuth 2.0 授权解决方案

## 📋 问题分析

### 1. 个人令牌 vs OAuth 授权对比

| 授权方式 | 有效期 | 安全性 | 复杂度 | 适用场景 |
|---------|--------|--------|--------|----------|
| 个人令牌 (PAT) | **30天** | 中等 | 简单 | 开发测试 |
| OAuth 2.0 | **可长期有效** | 高 | 中等 | 生产环境 |

### 2. OAuth 授权的优势

✅ **长期有效性**：
- 访问令牌虽然短期（通常1小时），但可通过刷新令牌自动续期
- 刷新令牌有效期更长（30天或更长），可实现长期无人值守运行

✅ **安全性更高**：
- 支持PKCE（Proof Key for Code Exchange）
- 令牌权限可精确控制
- 支持令牌撤销

✅ **自动化管理**：
- 可实现令牌自动刷新
- 避免手动更新令牌的麻烦

## 🧪 连通性测试结果

根据测试脚本的运行结果：

```
✅ https://api.coze.com/open_api/v2/chat - 连接成功 (200)
🔑 https://api.coze.com/v1/workflows/run - 需要认证 (401)
✅ https://www.coze.com - 连接成功 (200)
❓ https://api.coze.com/v1/chat - 端点不存在 (404)
```

**结论**：coze.cn **没有封禁** coze.com 的API访问，可以正常使用OAuth授权。

## 🔐 OAuth 2.0 实施方案

### 步骤1：创建OAuth应用

1. 登录 [coze.com](https://www.coze.com)
2. 进入 **开发者设置** → **OAuth应用**
3. 点击 **创建新应用**
4. 配置应用信息：
   - **应用名称**：自定义名称
   - **应用类型**：根据需求选择（推荐：Web应用程序）
   - **回调URL**：`http://localhost:8080/callback`（开发用）
   - **权限范围**：勾选 `workflow:run`

### 步骤2：获取OAuth凭证

完成应用创建后，获取：
- **Client ID**：应用标识符
- **Client Secret**：应用密钥（保密）

### 步骤3：实现授权流程

#### 方案A：使用提供的OAuth示例代码

```python
# 使用 oauth_example.py
from oauth_example import CozeOAuthManager

# 初始化OAuth管理器
oauth_manager = CozeOAuthManager(
    client_id="your_client_id",
    client_secret="your_client_secret"
)

# 获取授权URL
auth_url, state, code_verifier = oauth_manager.get_authorization_url()
print(f"请访问: {auth_url}")

# 用户授权后，使用授权码换取令牌
authorization_code = input("请输入授权码: ")
oauth_manager.exchange_code_for_tokens(authorization_code, code_verifier)

# 保存令牌
oauth_manager.save_tokens_to_file()
```

#### 方案B：集成到coze.cn插件

使用 `oauth_plugin.py`，在插件参数中提供：

```json
{
  "query": "用户查询内容",
  "access_token": "oauth_access_token",
  "refresh_token": "oauth_refresh_token",
  "client_id": "your_client_id",
  "client_secret": "your_client_secret",
  "bot_id": "your_bot_or_workflow_id"
}
```

### 步骤4：令牌管理策略

#### 自动刷新机制

```python
def ensure_valid_token(self):
    """确保令牌有效，自动刷新即将过期的令牌"""
    if self.token_expires_at and datetime.now() >= (self.token_expires_at - timedelta(minutes=5)):
        return self.refresh_access_token()
    return True
```

#### 令牌存储

- **开发环境**：本地文件存储
- **生产环境**：安全的密钥管理服务
- **coze.cn插件**：环境变量或安全配置

## 🛠️ 具体实施建议

### 对于您的使用场景

1. **短期解决方案**（立即可用）：
   - 继续使用个人令牌
   - 设置30天提醒，定期更新

2. **长期解决方案**（推荐）：
   - 实施OAuth 2.0授权
   - 使用提供的示例代码
   - 实现自动令牌刷新

### 迁移步骤

1. **第1周**：创建OAuth应用，测试授权流程
2. **第2周**：集成OAuth到现有插件
3. **第3周**：实现令牌自动刷新
4. **第4周**：部署到生产环境

## 📁 文件说明

### 已创建的文件

1. **`test_coze_com_access.py`**
   - 测试coze.com API连通性
   - 验证是否被封禁
   - 提供详细的连接测试报告

2. **`oauth_example.py`**
   - 完整的OAuth 2.0实现示例
   - 支持PKCE授权
   - 包含令牌刷新和存储功能

3. **`oauth_plugin.py`**
   - coze.cn插件的OAuth版本
   - 支持自动令牌刷新
   - 可直接在coze.cn中使用

### 使用方法

```bash
# 测试连通性
python test_coze_com_access.py

# OAuth授权演示
python oauth_example.py

# 在coze.cn中使用oauth_plugin.py替换现有插件
```

## 🔄 OAuth授权流程图

```
用户 → coze.cn插件 → OAuth授权 → coze.com API
  ↓         ↓           ↓            ↓
查询 → 检查令牌 → 自动刷新 → 返回结果
```

## ⚠️ 注意事项

1. **API端点**：根据测试结果，实际可用的API端点是 `/open_api/v2/chat`
2. **权限配置**：确保OAuth应用有足够的权限
3. **错误处理**：实现完善的错误处理和重试机制
4. **安全性**：妥善保管Client Secret和刷新令牌

## 🎯 总结

**回答您的问题**：

1. ✅ **OAuth授权可以长期有效**：通过刷新令牌机制实现长期无人值守运行
2. ✅ **coze.cn没有封禁coze.com**：测试显示API可正常访问
3. 💡 **建议使用OAuth 2.0**：更安全、更稳定的长期解决方案

使用提供的代码和方案，您可以实现稳定的长期API访问，避免30天令牌过期的困扰。