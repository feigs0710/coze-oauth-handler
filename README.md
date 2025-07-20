# Coze跨平台集成项目

## 📖 项目简介

本项目旨在实现在 **coze.cn** 插件中通过 **OAuth认证** 调用 **coze.com** 工作流的跨平台集成解决方案。

### 🎯 核心目标
- 在coze.cn插件中调用coze.com的工作流API
- 使用OAuth 2.0进行安全认证
- 提供健壮的错误处理和连接测试
- 支持多种API操作（执行工作流、聊天等）

## 🏗️ 项目结构

```
coze-oauth-integration/
├── 🔧 核心工具
│   ├── oauth_test_tool.py              # OAuth配置测试工具
│   ├── coze_oauth_integration.py       # OAuth集成模块
│   └── coze_connectivity_test_plugin.py # 连通性测试插件
│
├── 🏗️ 架构增强
│   ├── config_manager.py               # 统一配置管理
│   ├── dependency_injection.py         # 依赖注入容器
│   ├── metrics_collector.py            # 性能监控收集
│   └── integration_test_framework.py   # 集成测试框架
│
├── 📚 使用指南
│   ├── 快速开始指南.md                 # 5分钟快速上手
│   ├── OAuth应用创建指南.md             # OAuth应用创建详细步骤
│   ├── Coze.com OAuth配置截图指南.md    # 详细配置说明
│   ├── Vercel部署OAuth回调指南.md       # Vercel部署教程
│   └── 重定向URI配置指南.md             # 重定向URI配置说明
│
├── 🔧 开发指南
│   └── 代码质量提升建议.md             # 代码优化建议
│
├── 🧪 测试套件
│   ├── robust_test.py                  # 健壮性测试脚本
│   ├── final_test.py                   # 最终测试脚本
│   └── quick_test.py                   # 快速测试脚本
│
└── 📖 项目文档
    └── README.md                       # 项目总览
```

## 🚀 快速开始

### 方式一：5分钟快速配置（推荐）

跟随我们的快速指南，5分钟内完成配置：

📖 **[快速开始指南.md](快速开始指南.md)**

### 方式二：详细配置流程

#### 步骤1：部署OAuth回调处理

1. **部署到Vercel**（推荐）：
   - 参考：📖 **[Vercel部署OAuth回调指南.md](Vercel部署OAuth回调指南.md)**
   - 获得回调URL：`https://your-app.vercel.app/oauth/callback`

2. **本地开发**（可选）：
   - 使用：`http://localhost:8080/oauth/callback`
   - 参考：📖 **[重定向URI配置指南.md](重定向URI配置指南.md)**

#### 步骤2：创建Coze.com OAuth应用

1. **快速配置**：
   - 访问：[https://www.coze.com/open/oauth](https://www.coze.com/open/oauth)
   - 创建Web Application类型的Confidential客户端
   - 配置重定向URI为您的Vercel部署地址

2. **详细指南**：
   - 📖 **[Coze.com OAuth配置截图指南.md](Coze.com OAuth配置截图指南.md)**
   - 📖 **[OAuth应用创建指南.md](OAuth应用创建指南.md)**

#### 步骤3：测试OAuth配置

```bash
python oauth_test_tool.py
```

按提示输入您的Client ID和Client Secret，完成OAuth授权流程测试。

#### 步骤4：集成到coze.cn插件

```python
from coze_oauth_integration import CozeOAuthClient

# 创建OAuth客户端
client = CozeOAuthClient(
    client_id="your_client_id",
    client_secret="your_client_secret",
    redirect_uri="https://your-app.vercel.app/oauth/callback"
)

# 获取授权URL
auth_url = client.get_authorization_url()
print(f"请访问: {auth_url}")

# 使用授权码获取访问令牌
authorization_code = input("请输入授权码: ")
token_data = client.get_access_token(authorization_code)

# 调用coze.com API
response = client.call_api(
    method="GET",
    endpoint="/v1/workflows",
    access_token=token_data["access_token"]
)
```

## 🔧 核心功能

### OAuth认证模块 (`coze_oauth_integration.py`)

- ✅ **OAuth 2.0认证流程**：授权码模式
- ✅ **自动令牌管理**：获取、刷新、验证
- ✅ **API请求封装**：统一的请求处理
- ✅ **错误处理**：完善的异常处理机制

**支持的操作**：
- 执行工作流 (`execute_workflow`)
- 列出工作流 (`list_workflows`)
- 获取工作流信息 (`get_workflow`)
- 发送聊天消息 (`send_chat`)

### 测试工具 (`oauth_test_tool.py`)

- 🧪 **完整OAuth流程测试**
- 🌐 **自动回调服务器**
- 🔍 **API调用验证**
- 📊 **详细测试报告**

### 连通性测试 (`coze_connectivity_test_plugin.py`)

- 🌍 **网络连通性检测**
- 🔐 **API端点验证**
- 🛡️ **健壮性保障**（已通过全面测试）
- 📝 **详细日志记录**

## 🧪 测试套件

项目包含完整的测试套件，确保代码质量：

### 健壮性测试
```bash
# 运行所有健壮性测试
python robust_test.py

# 运行最终测试（无网络请求）
python final_test.py

# 运行快速测试
python quick_test.py
```

### 测试覆盖范围
- ✅ 参数验证（None值、缺失属性）
- ✅ 日志系统健壮性
- ✅ 异常处理机制
- ✅ 网络连接测试
- ✅ OAuth认证流程
- ✅ API调用功能

## 📋 配置要求

### 环境要求
- Python 3.7+
- 网络访问coze.com
- 可用端口（默认8080）

### OAuth应用配置
```
应用类型：Web Application
客户端类型：Confidential
重定向URI：http://localhost:8080/oauth/callback
权限范围：workflows:read, workflows:execute, chat:write, chat:read
```

### 环境变量（可选）
```bash
COZE_CLIENT_ID=your_client_id
COZE_CLIENT_SECRET=your_client_secret
COZE_REDIRECT_URI=http://localhost:8080/oauth/callback
```

## 🔒 安全注意事项

1. **保护敏感信息**：
   - 不要在代码中硬编码Client Secret
   - 使用环境变量或安全的配置管理
   - 定期轮换访问令牌

2. **生产环境部署**：
   - 使用HTTPS重定向URI
   - 实施适当的访问控制
   - 监控API使用情况

3. **错误处理**：
   - 实现令牌过期自动刷新
   - 处理API限流和错误响应
   - 提供用户友好的错误信息

## 🐛 故障排除

### 常见问题

**Q: 找不到开发者控制台入口？**
A: 确认使用coze.com（国际版），尝试直接访问：https://www.coze.com/open/oauth/apps

**Q: OAuth授权后回调失败？**
A: 检查重定向URI配置，确认为：`http://localhost:8080/oauth/callback`

**Q: API调用返回403错误？**
A: 检查权限范围配置，确认包含所需的权限（如`workflows:read`）

**Q: 令牌交换失败？**
A: 验证Client Secret是否正确，确认授权码未过期

### 调试工具

1. **运行连通性测试**：
   ```bash
   python coze_connectivity_test_plugin.py
   ```

2. **运行OAuth测试**：
   ```bash
   python oauth_test_tool.py
   ```

3. **查看详细日志**：
   - 测试工具会提供详细的错误信息
   - 检查网络连接和防火墙设置

## 📚 文档索引

### 🚀 快速上手
- 📋 **[快速开始指南.md](./快速开始指南.md)** - 5分钟快速配置
- 🔧 **[OAuth应用创建指南.md](./OAuth应用创建指南.md)** - 详细配置步骤
- 📸 **[Coze.com OAuth配置截图指南.md](./Coze.com OAuth配置截图指南.md)** - 图文配置说明

### 🌐 部署指南
- ☁️ **[Vercel部署OAuth回调指南.md](./Vercel部署OAuth回调指南.md)** - Vercel部署教程
- 🔗 **[重定向URI配置指南.md](./重定向URI配置指南.md)** - 重定向URI配置

### 🛠️ 核心工具
- 🔧 **[oauth_test_tool.py](./oauth_test_tool.py)** - OAuth配置测试工具
- 🔗 **[coze_oauth_integration.py](./coze_oauth_integration.py)** - OAuth集成核心模块
- 🧪 **[coze_connectivity_test_plugin.py](./coze_connectivity_test_plugin.py)** - 连通性测试插件

### 🏗️ 架构增强
- ⚙️ **[config_manager.py](./config_manager.py)** - 统一配置管理
- 💉 **[dependency_injection.py](./dependency_injection.py)** - 依赖注入容器
- 📊 **[metrics_collector.py](./metrics_collector.py)** - 性能监控收集
- 🧪 **[integration_test_framework.py](./integration_test_framework.py)** - 集成测试框架

### 🔧 开发指南
- 💡 **[代码质量提升建议.md](./代码质量提升建议.md)** - 代码优化建议

### 🧪 测试套件
- ⚡ **[quick_test.py](./quick_test.py)** - 快速功能测试
- 🛡️ **[robust_test.py](./robust_test.py)** - 健壮性测试
- ✅ **[final_test.py](./final_test.py)** - 最终集成测试

## 🤝 贡献

欢迎提交Issue和Pull Request来改进项目！

## 📄 许可证

本项目采用MIT许可证。

---

**🎉 现在您可以开始在coze.cn插件中调用coze.com的工作流了！**

如有问题，请参考相关文档或使用提供的测试工具进行诊断。