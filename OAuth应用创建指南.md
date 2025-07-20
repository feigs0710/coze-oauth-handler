# Coze.com OAuth应用创建指南

## 概述

根据您的需求，我们需要在coze.com上创建OAuth应用，以便在coze.cn的插件中通过API调用coze.com的工作流。

## 第一步：访问Coze.com开发者控制台

### 1. 访问Coze.com开发者控制台

1. 打开浏览器，访问 [https://www.coze.com](https://www.coze.com)
2. 使用您的账号登录（支持Google、GitHub等第三方登录）
3. 登录后，点击右上角的用户头像
4. 在下拉菜单中选择 **"Developer Console"** 或 **"开发者控制台"**
   - 如果没有看到此选项，可能需要先申请开发者权限
   - 或者直接访问：[https://www.coze.com/open/oauth](https://www.coze.com/open/oauth)

### 2. 创建OAuth应用

1. 在开发者控制台中，找到 **"OAuth Apps"** 或 **"OAuth应用"** 选项
2. 点击 **"Create App"** 或 **"创建应用"** 按钮
3. 填写应用基本信息：

#### 应用基本信息
- **应用名称 (App Name)**: 输入您的应用名称，例如："Coze.cn插件集成"
- **应用描述 (Description)**: 简要描述应用用途，例如："用于coze.cn插件调用coze.com工作流"
- **应用类型 (Application Type)**: 选择 **"Web Application"**
- **客户端类型 (Client Type)**: 选择 **"Confidential"**（机密客户端）

#### OAuth配置

**重定向URI (Redirect URI)**:
- 由于您已经在Vercel部署了OAuth处理页面，请输入您的Vercel URL
- 格式应该是：`https://your-app-name.vercel.app/oauth/callback`
- 例如：`https://coze-oauth-handler-eta48.vercel.app/oauth/callback`
- **注意**：必须使用HTTPS协议，HTTP在生产环境中不被允许

**权限范围 (Scopes)**:
选择您需要的权限，推荐选择：
- `read:user` - 读取用户基本信息
- `read:workspace` - 读取工作空间信息
- `read:workflow` - 读取工作流信息
- `write:workflow` - 执行工作流
- `read:chat` - 读取聊天信息
- `write:chat` - 发送聊天消息

### 3. 获取应用凭据

1. 创建应用后，系统会生成：
   - **Client ID** (客户端ID)
   - **Client Secret** (客户端密钥)

2. **重要**：请立即复制并安全保存这些凭据
   - Client Secret 只会显示一次
   - 如果丢失，需要重新生成

3. 将这些凭据记录在安全的地方，稍后配置时需要使用

### 4. 验证配置

完成上述配置后，您的OAuth应用应该包含：
- ✅ 应用名称和描述
- ✅ 重定向URI（指向您的Vercel部署）
- ✅ 必要的权限范围
- ✅ Client ID 和 Client Secret

### 5. 下一步

配置完成后，您可以：
1. 使用我们提供的 `oauth_test_tool.py` 测试OAuth配置
2. 将凭据集成到您的coze.cn插件中
3. 开始调用coze.com的工作流API

---

## 常见问题

**Q: 找不到开发者控制台入口？**
A: 尝试直接访问 https://www.coze.com/open/oauth 或联系Coze支持申请开发者权限。

**Q: 重定向URI验证失败？**
A: 确保URL完全匹配，包括协议(https)、域名、端口和路径。

**Q: Client Secret丢失了怎么办？**
A: 在应用设置中点击"重新生成密钥"，但需要更新所有使用旧密钥的地方。

---

## 详细配置步骤

### 步骤1：访问coze.com并登录

1. 打开浏览器，访问 [https://www.coze.com](https://www.coze.com)
2. 点击右上角的 "Sign In" 或 "登录" 按钮
3. 选择登录方式（推荐使用Google或GitHub登录）
4. 完成登录流程

### 步骤2：进入开发者控制台

1. 登录后，点击右上角的用户头像
2. 在下拉菜单中查找 "Developer" 或 "开发者" 相关选项
3. 如果没有找到，请直接访问：[https://www.coze.com/open/oauth](https://www.coze.com/open/oauth)
4. 首次访问可能需要同意开发者协议

### 步骤3：创建OAuth应用

1. 在开发者控制台页面，找到 "OAuth Apps" 或类似选项
2. 点击 "Create App" 或 "新建应用" 按钮
3. 填写以下信息：

**基本信息**：
- **App Name**: `Coze.cn插件集成`
- **Description**: `用于coze.cn插件调用coze.com工作流`
- **Application Type**: `Web Application`
- **Client Type**: `Confidential`

**OAuth配置**：
- **Redirect URI**: 输入您的Vercel URL，格式如：
  ```
  https://your-vercel-app.vercel.app/oauth/callback
  ```
  
**权限范围 (Scopes)**：
选择以下权限（根据实际需要）：
- ☑️ `read:user` - 读取用户信息
- ☑️ `read:workspace` - 读取工作空间
- ☑️ `read:workflow` - 读取工作流
- ☑️ `write:workflow` - 执行工作流
- ☑️ `read:chat` - 读取聊天记录
- ☑️ `write:chat` - 发送消息

### 步骤4：保存应用凭据

创建成功后，您将获得：
- **Client ID**: `your_client_id_here`
- **Client Secret**: `your_client_secret_here`

**⚠️ 重要提醒**：
- Client Secret 只显示一次，请立即复制保存
- 建议保存到密码管理器或安全的配置文件中
- 不要将这些凭据提交到公开的代码仓库

### 步骤5：测试配置

使用我们提供的测试工具验证配置：

```bash
python oauth_test_tool.py
```

按提示输入您刚才获得的 Client ID 和 Client Secret。

---

## 配置验证清单

完成配置后，请确认以下项目：

- ✅ 已成功创建OAuth应用
- ✅ 重定向URI指向您的Vercel部署
- ✅ 已选择必要的权限范围
- ✅ 已安全保存Client ID和Client Secret
- ✅ 重定向URI使用HTTPS协议
- ✅ 应用状态为"Active"或"已激活"

---

## 故障排除

### 问题1：找不到开发者控制台
**解决方案**：
1. 确认账号已完成邮箱验证
2. 尝试直接访问：https://www.coze.com/open/oauth
3. 联系Coze支持申请开发者权限

### 问题2：重定向URI验证失败
**解决方案**：
1. 确保URL完全匹配（包括协议、域名、路径）
2. 检查是否使用了HTTPS协议
3. 确认Vercel部署成功且可访问

### 问题3：权限不足
**解决方案**：
1. 检查选择的权限范围是否足够
2. 确认应用类型选择正确
3. 重新生成访问令牌

---

## 下一步操作

配置完成后，您可以：

1. **测试OAuth流程**：
   ```bash
   python oauth_test_tool.py
   ```

2. **集成到插件**：
   ```python
   from coze_oauth_integration import CozeOAuthClient
   
   client = CozeOAuthClient(
       client_id="your_client_id",
       client_secret="your_client_secret",
       redirect_uri="https://your-app.vercel.app/oauth/callback"
   )
   ```

3. **开始调用API**：
   参考 `coze_connectivity_test_plugin.py` 中的示例代码

## 第二步：创建OAuth应用

### 1. 进入应用管理页面

在开发者控制台中：
1. **查找OAuth应用管理**：
   - 寻找"OAuth Apps"、"应用管理"或"My Apps"等选项
   - 可能在侧边栏或顶部导航中
2. **点击"创建应用"或"New App"按钮**

### 2. 基本信息配置

#### 必填信息：

根据您的截图，在创建应用页面需要填写以下信息：

**App type（应用类型）**
- 选择：`Normal`（普通应用）

**Client type（客户端类型）**
- 推荐选择：`Web application`（Web应用程序）
- 原因：适合服务器端OAuth流程，安全性更高

**App name（应用名称）**
- 建议：`Coze CN Plugin Integration`
- 或者：`工作流API集成应用`

**App description（应用描述）**
- 建议填写：
```
This application is used to integrate Coze.com workflows with Coze.cn plugins through OAuth authentication. It enables secure API access to execute workflows from external applications.

此应用用于通过OAuth认证将Coze.com工作流与Coze.cn插件集成，实现从外部应用安全访问和执行工作流的功能。
```

### 2. 配置步骤详解

1. **选择应用类型**
   - 点击"App type"下拉菜单
   - 选择"Normal"

2. **选择客户端类型**
   - 点击"Client type"下拉菜单
   - 选择"Web application"

3. **填写应用名称**
   - 在"App name"字段输入应用名称
   - 注意：名称长度限制为20个字符

4. **填写应用描述**
   - 在"App description"字段输入详细描述
   - 注意：描述长度限制为255个字符

5. **点击创建**
   - 点击"Create and continue"按钮继续下一步

## 第二步：配置OAuth设置

创建应用后，您需要配置以下OAuth相关设置：

### 1. 

**开发环境：**
```
http://localhost:8080/oauth/callback
```

**生产环境：**
```
https://your-domain.com/oauth/callback
```

### 2. 权限范围（Scopes）

#### 重定向URI (Redirect URI)
这是OAuth认证完成后，Coze会重定向用户的地址：

**测试环境配置**：
```
http://localhost:8080/oauth/callback
```

**生产环境配置**：
```
https://yourdomain.com/oauth/callback
```

**重要提示**：
- 必须使用HTTPS（生产环境）
- 端口号要与您的应用服务器一致
- 路径可以自定义，但要与代码中的配置保持一致

#### 权限范围 (Scopes)
根据您的需求选择合适的权限：

**推荐权限组合**：
- ✅ `workflows:read` - 读取工作流列表和详情
- ✅ `workflows:execute` - 执行工作流
- ✅ `chat:write` - 发送聊天消息
- ✅ `chat:read` - 读取聊天记录

**可选权限**：
- `bots:read` - 读取机器人信息
- `spaces:read` - 读取空间信息

### 3. 获取应用凭据

创建完成后，您将获得：
- **Client ID**：公开标识符
- **Client Secret**：私密密钥（请妥善保管）

## 第三步：实现OAuth认证流程

### 1. 授权URL构建

```python
def get_authorization_url(client_id, redirect_uri, state=None):
    """
    构建OAuth授权URL
    """
    base_url = "https://www.coze.com/api/permission/oauth2/authorize"
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "workflows:read workflows:execute",
        "state": state or "random_state_string"
    }
    
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"{base_url}?{query_string}"
```

### 2. 访问令牌获取

```python
import requests

def get_access_token(client_id, client_secret, code, redirect_uri):
    """
    使用授权码获取访问令牌
    """
    token_url = "https://www.coze.com/api/permission/oauth2/token"
    
    data = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    response = requests.post(token_url, data=data, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"获取访问令牌失败: {response.text}")
```

### 3. API调用示例

```python
def call_workflow_api(access_token, workflow_id, parameters=None):
    """
    调用工作流API
    """
    api_url = f"https://api.coze.com/v1/workflows/{workflow_id}/run"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "parameters": parameters or {}
    }
    
    response = requests.post(api_url, json=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API调用失败: {response.text}")
```

## 第四步：测试OAuth配置

### 使用OAuth测试工具

我已经为您创建了一个专门的测试工具 `oauth_test_tool.py`，可以帮助您验证OAuth配置：

#### 完整测试（推荐）：
```bash
python oauth_test_tool.py
```

#### 快速配置测试：
```bash
python oauth_test_tool.py --quick
```

#### 测试流程：
1. **输入OAuth配置**：Client ID 和 Client Secret
2. **自动启动回调服务器**：监听 localhost:8080
3. **打开授权页面**：自动在浏览器中打开
4. **完成授权**：在浏览器中点击授权
5. **获取令牌**：自动交换访问令牌
6. **测试API**：调用工作流列表API验证

### 测试成功标志

✅ **配置正确的表现**：
- OAuth客户端配置完成
- 回调服务器启动成功
- 浏览器正常打开授权页面
- 授权后成功获取授权码
- 令牌交换成功
- API调用返回工作流列表

❌ **常见问题及解决**：

**问题1：无法打开授权页面**
- 检查Client ID是否正确
- 确认使用的是coze.com而非coze.cn

**问题2：授权后回调失败**
- 确认重定向URI配置为：`http://localhost:8080/oauth/callback`
- 检查端口8080是否被占用

**问题3：令牌交换失败**
- 检查Client Secret是否正确
- 确认授权码未过期（通常60秒内有效）

**问题4：API调用失败**
- 检查权限范围是否包含`workflows:read`
- 确认账户下有可访问的工作流

## 第五步：集成到Coze.cn插件

### 使用集成模块

使用提供的 `coze_oauth_integration.py` 模块：

```python
from coze_oauth_integration import CozePluginIntegration

# 初始化集成
integration = CozePluginIntegration(
    client_id="your_client_id",
    client_secret="your_client_secret",
    redirect_uri="your_redirect_uri"
)

# 在插件中使用
def plugin_handler(args):
    # 执行工作流
    result = integration.handle_request({
        "action": "execute_workflow",
        "workflow_id": "your_workflow_id",
        "parameters": {"input": "test"}
    })
    return result
```

### 环境变量配置

在您的插件中设置以下环境变量：

```python
# OAuth配置
COZE_CLIENT_ID = "your_client_id_here"
COZE_CLIENT_SECRET = "your_client_secret_here"
COZE_REDIRECT_URI = "http://localhost:8080/oauth/callback"
```

### 插件集成代码

```python
class CozeWorkflowIntegration:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.access_token = None
    
    def authenticate(self):
        """启动OAuth认证流程"""
        auth_url = self.get_authorization_url()
        print(f"请访问以下URL进行授权: {auth_url}")
        
        # 在实际应用中，这里应该是Web服务器处理回调
        code = input("请输入授权码: ")
        
        token_response = self.get_access_token(code)
        self.access_token = token_response["access_token"]
        
        return self.access_token
    
    def execute_workflow(self, workflow_id, parameters=None):
        """执行工作流"""
        if not self.access_token:
            raise Exception("请先进行OAuth认证")
        
        return self.call_workflow_api(workflow_id, parameters)
```

### 生产环境部署

1. **更新重定向URI**：
   - 将测试用的 `localhost:8080` 改为实际域名
   - 确保使用HTTPS

2. **配置管理**：
   - 使用配置文件或环境变量
   - 不要硬编码敏感信息

3. **监控和日志**：
   - 记录API调用情况
   - 监控令牌使用和刷新
   - 设置异常告警

## 安全注意事项

1. **Client Secret保护**
   - 永远不要在客户端代码中暴露Client Secret
   - 使用环境变量或安全的配置管理系统

2. **State参数**
   - 始终使用随机的state参数防止CSRF攻击
   - 验证回调中的state参数

3. **HTTPS使用**
   - 生产环境中必须使用HTTPS
   - 重定向URI必须使用HTTPS

4. **令牌管理**
   - 安全存储访问令牌
   - 实现令牌刷新机制
   - 设置合适的令牌过期时间

## 测试步骤

1. **创建测试应用**
   - 按照上述步骤创建OAuth应用
   - 记录Client ID和Client Secret

2. **本地测试**
   - 运行OAuth认证流程
   - 验证能否成功获取访问令牌

3. **API测试**
   - 使用获取的令牌调用工作流API
   - 验证返回结果

## 常见问题

**Q: 如何处理令牌过期？**
A: 实现refresh token机制，或重新进行OAuth认证流程。

**Q: 可以在coze.cn插件中直接使用吗？**
A: 需要根据coze.cn插件的运行环境调整OAuth流程，可能需要使用设备码流程。

**Q: 如何调试OAuth问题？**
A: 检查重定向URI配置、权限范围设置，查看详细的错误响应。

---

按照这个指南，您应该能够成功创建OAuth应用并实现coze.cn插件与coze.com工作流的集成。如果遇到具体问题，请提供详细的错误信息以便进一步协助。