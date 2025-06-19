# GitHub Enterprise SCIM 用户创建工具

该工具可以通过读取CSV文件，使用GitHub Enterprise的SCIM API接口实现用户的创建操作。

## 功能特点

- 读取CSV文件中的用户信息
- 通过GitHub SCIM接口创建新用户
- 支持以下用户属性：
  - userName (必填)
  - displayName (必填)
  - emails (可多个邮箱，使用分号分隔)
  - roles (可多个角色，使用分号分隔)

## 环境要求

- Python 3.6+
- 依赖库：requests

## 安装

1. 克隆本仓库
2. 安装依赖库：

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 准备CSV文件

创建一个包含用户信息的CSV文件，格式如下：

```
userName,displayName,emails,roles
johndoe,John Doe,john.doe@example.com,developer;admin
janedoe,Jane Doe,jane.doe@example.com;jane.personal@example.net,manager;developer
bobsmith,Bob Smith,bob.smith@example.com,analyst
```

- `userName`: 用户的登录名 (必填)
- `displayName`: 用户的显示名称 (必填)
- `emails`: 用户的邮箱地址，多个邮箱使用分号(;)分隔
- `roles`: 用户的角色，多个角色使用分号(;)分隔

### 2. 运行脚本

```bash
python github_scim_user_management.py --csv example_users.csv --url https://github.example.com --token YOUR_OAUTH_TOKEN
```

### 参数说明
- `--csv`: CSV文件路径
- `--url`: GitHub Enterprise URL
- `--token`: GitHub OAuth令牌，需要具有SCIM权限

## 日志

脚本执行过程中的日志会同时输出到控制台和保存到 `github_scim.log` 文件中。

## 安全提示

- 请妥善保管您的OAuth令牌，不要将其硬编码在脚本中或提交到版本控制系统
- 建议将令牌存储在环境变量中，并通过环境变量传递给脚本

## 常见问题

1. **获取OAuth令牌**：
   - 在GitHub Enterprise中，导航至用户设置 -> 开发者设置 -> 个人访问令牌
   - 创建新令牌，并确保勾选SCIM权限

2. **CSV格式错误**：
   - 确保CSV文件使用UTF-8编码
   - 第一行必须是标题行，包含必要的字段名

3. **API连接问题**：
   - 检查GitHub Enterprise URL是否正确
   - 验证OAuth令牌是否有效且具有正确的权限范围
