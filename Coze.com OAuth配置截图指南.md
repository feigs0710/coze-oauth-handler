# Coze.com OAuth配置截图指南

本指南通过详细的步骤说明和配置要点，帮助您在coze.com上正确配置OAuth应用。

## 📋 配置前准备

在开始配置之前，请确保您已经：

- ✅ 拥有coze.com账号并已登录
- ✅ 已在Vercel部署OAuth回调处理页面
- ✅ 获得了Vercel部署的完整URL

## 🚀 详细配置步骤

### 步骤1：访问Coze.com开发者控制台

1. **打开coze.com**
   - 访问：https://www.coze.com
   - 确保使用正确的国际版网站（不是coze.cn）

2. **登录账号**
   - 点击右上角 "Sign In" 按钮
   - 推荐使用Google或GitHub登录
   - 完成登录流程

3. **进入开发者控制台**
   - 登录后，点击右上角用户头像
   - 查找 "Developer" 或 "API" 相关选项
   - 如果找不到，直接访问：https://www.coze.com/open/oauth

### 步骤2：创建OAuth应用

#### 2.1 开始创建应用

在开发者控制台页面：
1. 找到 "OAuth Apps" 或 "应用管理" 选项
2. 点击 "Create App" 或 "新建应用" 按钮
3. 进入应用创建表单

#### 2.2 填写应用基本信息

**应用名称 (App Name)**
```
Coze.cn插件集成
```

**应用描述 (Description)**
```
用于coze.cn插件调用coze.com工作流API，实现跨平台集成功能
```

**应用类型 (Application Type)**
- 选择：`Web Application`
- 这是最适合服务器端集成的类型

**客户端类型 (Client Type)**
- 选择：`Confidential`
- 机密客户端，适合能安全存储密钥的应用

#### 2.3 配置OAuth设置

**重定向URI (Redirect URI)**

这是最关键的配置项，请按以下格式填写：

```
https://your-vercel-app.vercel.app/oauth/callback
```

**示例**：
```
https://coze-oauth-handler-eta48.vercel.app/oauth/callback
```

**⚠️ 重要注意事项**：
- 必须使用 `https://` 协议
- 域名必须与您的Vercel部署完全匹配
- 路径必须是 `/oauth/callback`
- 不能有多余的斜杠或参数

**权限范围 (Scopes)**

根据您的需求选择以下权限：

**基础权限**（推荐全选）：
- ☑️ `read:user` - 读取用户基本信息
- ☑️ `read:workspace` - 读取工作空间信息

**工作流相关**：
- ☑️ `read:workflow` - 读取工作流信息
- ☑️ `write:workflow` - 执行工作流
- ☑️ `read:bot` - 读取机器人信息
- ☑️ `write:bot` - 操作机器人

**聊天相关**：
- ☑️ `read:chat` - 读取聊天记录
- ☑️ `write:chat` - 发送聊天消息

**文件相关**（可选）：
- ☐ `read:file` - 读取文件
- ☐ `write:file` - 上传文件

### 步骤3：保存并获取凭据

#### 3.1 提交应用创建

1. 检查所有信息是否正确
2. 点击 "Create" 或 "创建" 按钮
3. 等待应用创建完成

#### 3.2 获取应用凭据

创建成功后，您将看到：

**Client ID（客户端ID）**
```
示例：1234567890abcdef
```

**Client Secret（客户端密钥）**
```
示例：abcdef1234567890_secret_key_here
```

**⚠️ 重要提醒**：
- Client Secret 只显示一次，请立即复制保存
- 建议保存到密码管理器或安全的配置文件中
- 不要将密钥提交到公开的代码仓库
- 如果丢失，需要重新生成（会使旧密钥失效）

### 步骤4：验证配置

#### 4.1 检查应用状态

确认以下信息：
- ✅ 应用状态：Active（激活）
- ✅ 应用类型：Web Application
- ✅ 客户端类型：Confidential
- ✅ 重定向URI：指向您的Vercel部署
- ✅ 权限范围：已选择必要权限

#### 4.2 测试重定向URI

在浏览器中访问您的重定向URI：
```
https://your-vercel-app.vercel.app/oauth/callback
```

应该看到OAuth处理页面，而不是404错误。

## 🔧 配置示例

### 完整配置示例

```yaml
应用配置:
  名称: "Coze.cn插件集成"
  描述: "用于coze.cn插件调用coze.com工作流API"
  类型: "Web Application"
  客户端类型: "Confidential"
  
OAuth配置:
  重定向URI: "https://coze-oauth-handler-eta48.vercel.app/oauth/callback"
  权限范围:
    - "read:user"
    - "read:workspace"
    - "read:workflow"
    - "write:workflow"
    - "read:chat"
    - "write:chat"
    
应用凭据:
  Client ID: "your_client_id_here"
  Client Secret: "your_client_secret_here"
```

## 🚨 常见错误及解决方案

### 错误1：找不到开发者控制台

**现象**：登录后找不到开发者或API相关选项

**解决方案**：
1. 确认使用的是 coze.com（不是 coze.cn）
2. 确认账号已完成邮箱验证
3. 直接访问：https://www.coze.com/open/oauth
4. 联系Coze支持申请开发者权限

### 错误2：重定向URI验证失败

**现象**：提示重定向URI无效或不匹配

**解决方案**：
1. 检查协议：必须是 `https://`
2. 检查域名：必须与Vercel部署完全匹配
3. 检查路径：必须是 `/oauth/callback`
4. 检查拼写：不能有多余的空格或字符
5. 测试Vercel部署是否正常访问

### 错误3：权限不足

**现象**：后续API调用时提示权限不足

**解决方案**：
1. 返回应用设置，检查权限范围
2. 确保选择了必要的权限
3. 重新生成访问令牌
4. 检查API调用时使用的权限范围

### 错误4：Client Secret丢失

**现象**：忘记保存或丢失了Client Secret

**解决方案**：
1. 在应用设置中找到 "重新生成密钥" 选项
2. 点击生成新的Client Secret
3. 立即复制并保存新密钥
4. 更新所有使用旧密钥的配置

## 📝 配置检查清单

完成配置后，请逐项检查：

**应用基本信息**：
- ☐ 应用名称已填写
- ☐ 应用描述已填写
- ☐ 应用类型选择 "Web Application"
- ☐ 客户端类型选择 "Confidential"

**OAuth配置**：
- ☐ 重定向URI格式正确
- ☐ 重定向URI指向Vercel部署
- ☐ 使用HTTPS协议
- ☐ 路径为 `/oauth/callback`

**权限配置**：
- ☐ 已选择 `read:user`
- ☐ 已选择 `read:workspace`
- ☐ 已选择 `read:workflow`
- ☐ 已选择 `write:workflow`
- ☐ 根据需要选择其他权限

**凭据管理**：
- ☐ 已复制并保存Client ID
- ☐ 已复制并保存Client Secret
- ☐ 凭据存储在安全位置
- ☐ 未将凭据提交到公开仓库

**验证测试**：
- ☐ 应用状态为 "Active"
- ☐ 重定向URI可正常访问
- ☐ 准备进行OAuth测试

## 🎯 下一步操作

配置完成后，您可以：

1. **测试OAuth流程**：
   ```bash
   python oauth_test_tool.py
   ```

2. **集成到插件**：
   使用获得的Client ID和Client Secret配置您的coze.cn插件

3. **开始API调用**：
   参考项目中的示例代码开始调用coze.com的API

---

**💡 提示**：建议将此配置信息保存到项目文档中，便于团队成员参考和后续维护。