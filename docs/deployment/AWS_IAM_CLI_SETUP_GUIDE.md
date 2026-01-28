# AWS IAM 用户设置与 CLI 访问调试指南

## 文档信息

- **创建日期**: 2026-01-28
- **维护者**: Sheldon
- **适用场景**: AWS IAM 用户创建、CLI 配置、权限调试

## 目录

1. [AWS 账号架构说明](#aws-账号架构说明)
2. [创建 IAM 用户](#创建-iam-用户)
3. [配置本地 CLI](#配置本地-cli)
4. [权限检查与调试](#权限检查与调试)
5. [常见问题解决](#常见问题解决)
6. [安全最佳实践](#安全最佳实践)

---

## AWS 账号架构说明

### 账号层级结构

```
AWS 账号（Account ID: 858766041545）
├── Root 用户（邮箱登录，应很少使用）
└── IAM 用户（子用户）
    ├── xiaodongyan（主账号用户）
    └── sheldon2026（新创建的开发用户）
```

### 关键概念

#### 1. AWS 账号 (Account)
- **账号 ID**: `858766041545`（或显示为 `8587-6604-1545`）
- 这是你的 AWS 主账号
- 只有一个
- 包含所有资源（EC2、S3、RDS 等）
- 对应一个账单

#### 2. Root 用户
- 用注册时的邮箱登录
- 拥有完全控制权限
- **应该很少使用**（仅用于账户级别设置）

#### 3. IAM 用户
- 在 AWS 账号下创建的子用户
- 可以有不同的权限
- 适合日常操作
- 符合安全最佳实践

---

## 创建 IAM 用户

### 步骤 1: 进入 IAM 控制台

```
AWS Console → Services → IAM → Users → Create user
```

### 步骤 2: 用户详情

**用户名**: `sheldon2026`

**Console 访问**:
- ✅ 勾选 "Provide user access to the AWS Management Console"
- 选择 "I want to create an IAM user"

### 步骤 3: 设置权限

推荐通过**用户组**管理权限：

#### 方式 1: 加入用户组（推荐）
```
创建或选择用户组 → 附加策略到组 → 用户自动继承组权限
```

**示例：**
- 用户组: `knowledgedemo`
- 附加策略: `AdministratorAccess`
- 用户: `sheldon2026` 加入该组

#### 方式 2: 直接附加策略
```
直接给用户附加策略（不推荐，难以批量管理）
```

**常用策略：**
- `AdministratorAccess`: 完全管理权限（谨慎使用）
- `PowerUserAccess`: 除 IAM 外的完全权限
- `AmazonEC2FullAccess`: EC2 完全访问
- `ReadOnlyAccess`: 只读权限

### 步骤 4: 审核并创建

- 检查配置
- 点击 "Create user"

### 步骤 5: 设置 Console 密码

创建用户后：
1. 进入用户详情页
2. 点击 "Security credentials" 标签
3. 在 "Console password" 部分设置密码
4. ✅ 建议勾选 "User must create a new password at next sign-in"

---

## 创建 Access Keys

### 何时需要 Access Keys

- 需要使用 AWS CLI
- 需要在代码中调用 AWS SDK
- 需要编程方式访问 AWS 服务

### 创建步骤

#### 1. 进入 Security credentials
```
IAM → Users → sheldon2026 → Security credentials 标签
```

#### 2. 创建 Access Key
- 点击 "Create access key"
- 选择用途: **Command Line Interface (CLI)**
- ✅ 勾选确认框
- 点击 "Next"

#### 3. 添加描述（可选）
```
Description tag: Local development CLI
```

#### 4. 下载凭证 ⚠️

**会显示：**
- Access key ID: `<your-access-key-id>`
- Secret access key: `<your-secret-access-key>`（只显示一次！）

**保存方式：**
- ✅ 点击 "Download .csv file"（强烈推荐）
- 或手动复制保存

⚠️ **重要**: Secret Access Key 关闭后无法再查看！

---

## 配置本地 CLI

### 凭证文件位置

```bash
~/.aws/credentials  # 存储 Access Keys
~/.aws/config       # 存储配置（region、output 等）
```

### 方法 1: 使用 AWS CLI 配置（推荐）

```bash
# 交互式配置
aws configure

# 输入以下信息：
AWS Access Key ID [None]: <your-access-key-id>
AWS Secret Access Key [None]: <your-secret-access-key>
Default region name [None]: ap-southeast-2
Default output format [None]: json
```

### 方法 2: 手动编辑配置文件

#### 编辑 `~/.aws/credentials`

```ini
[default]
aws_access_key_id = <your-access-key-id>
aws_secret_access_key = <your-secret-access-key>

[sheldon2026]
aws_access_key_id = <your-access-key-id>
aws_secret_access_key = <your-secret-access-key>
```

#### 编辑 `~/.aws/config`

```ini
[default]
region = ap-southeast-2
output = json

[profile sheldon2026]
region = ap-southeast-2
output = json
```

### 方法 3: 使用环境变量

```bash
export AWS_ACCESS_KEY_ID=<your-access-key-id>
export AWS_SECRET_ACCESS_KEY=<your-secret-access-key>
export AWS_DEFAULT_REGION=ap-southeast-2
```

### 使用多个 Profiles

```bash
# 使用特定 profile
aws s3 ls --profile sheldon2026

# 设置默认 profile（会话级别）
export AWS_PROFILE=sheldon2026
aws s3 ls

# 永久设置（添加到 ~/.bashrc 或 ~/.zshrc）
echo 'export AWS_PROFILE=sheldon2026' >> ~/.zshrc
```

---

## 权限检查与调试

### 基础检查命令

#### 1. 验证凭证是否有效

```bash
aws sts get-caller-identity
```

**预期输出：**
```json
{
    "UserId": "AIDA4P4TR4HES6FX4APQK",
    "Account": "858766041545",
    "Arn": "arn:aws:iam::858766041545:user/sheldon2026"
}
```

#### 2. 获取当前用户信息

```bash
aws iam get-user
```

**预期输出：**
```json
{
    "User": {
        "UserName": "sheldon2026",
        "UserId": "AIDA4P4TR4HES6FX4APQK",
        "Arn": "arn:aws:iam::858766041545:user/sheldon2026",
        "CreateDate": "2026-01-28T09:11:34+00:00",
        ...
    }
}
```

### 权限检查命令

#### 3. 查看直接附加的策略

```bash
aws iam list-attached-user-policies --user-name sheldon2026
```

**输出示例：**
```json
{
    "AttachedPolicies": [
        {
            "PolicyName": "IAMUserChangePassword",
            "PolicyArn": "arn:aws:iam::aws:policy/IAMUserChangePassword"
        }
    ]
}
```

#### 4. 查看内联策略

```bash
aws iam list-user-policies --user-name sheldon2026
```

#### 5. 查看用户组（重要！）

```bash
# 查看用户所属的组
aws iam list-groups-for-user --user-name sheldon2026
```

**输出示例：**
```json
{
    "Groups": [
        {
            "GroupName": "knowledgedemo",
            "Arn": "arn:aws:iam::858766041545:group/knowledgedemo"
        }
    ]
}
```

#### 6. 查看用户组的权限

```bash
# 查看组附加的策略
aws iam list-attached-group-policies --group-name knowledgedemo

# 查看组的内联策略
aws iam list-group-policies --group-name knowledgedemo
```

**输出示例：**
```json
{
    "AttachedPolicies": [
        {
            "PolicyName": "AdministratorAccess",
            "PolicyArn": "arn:aws:iam::aws:policy/AdministratorAccess"
        }
    ]
}
```

### 权限生效逻辑

用户的**最终权限** = 用户直接附加的策略 + 用户组的策略

**示例：**
- 用户 `sheldon2026` 直接附加: `IAMUserChangePassword`
- 用户组 `knowledgedemo` 附加: `AdministratorAccess`
- **最终权限**: 管理员权限（因为组权限更高）

### 测试具体服务权限

#### 测试 EC2 访问

```bash
# 列出所有区域
aws ec2 describe-regions

# 列出实例
aws ec2 describe-instances
```

#### 测试 S3 访问

```bash
# 列出所有 bucket
aws s3 ls

# 列出特定 bucket 内容
aws s3 ls s3://your-bucket-name/
```

#### 测试 IAM 访问

```bash
# 列出所有用户
aws iam list-users

# 列出所有角色
aws iam list-roles
```

---

## 常见问题解决

### 问题 1: "The config profile (xxx) could not be found"

**症状：**
```bash
$ aws sts get-caller-identity
The config profile (MS-Dev-Xiaodong) could not be found
```

**原因：**
环境变量 `AWS_PROFILE` 或 `AWS_DEFAULT_PROFILE` 引用了不存在的 profile。

**解决方案：**

```bash
# 检查环境变量
env | grep AWS

# 清除环境变量
unset AWS_PROFILE
unset AWS_DEFAULT_PROFILE

# 重新测试
aws sts get-caller-identity
```

**永久解决：**
检查并清理 `~/.bashrc` 或 `~/.zshrc` 中的 AWS 相关环境变量。

### 问题 2: "Access Denied" 或权限不足

**症状：**
```bash
$ aws ec2 describe-instances
An error occurred (UnauthorizedOperation) when calling the DescribeInstances operation
```

**排查步骤：**

1. **确认当前用户：**
   ```bash
   aws sts get-caller-identity
   ```

2. **检查直接附加的策略：**
   ```bash
   aws iam list-attached-user-policies --user-name $(aws iam get-user --query 'User.UserName' --output text)
   ```

3. **检查用户组（重要！）：**
   ```bash
   # 获取当前用户名
   USER_NAME=$(aws iam get-user --query 'User.UserName' --output text)

   # 查看用户组
   aws iam list-groups-for-user --user-name $USER_NAME

   # 查看组权限（替换 GROUP_NAME）
   aws iam list-attached-group-policies --group-name GROUP_NAME
   ```

4. **检查内联策略：**
   ```bash
   aws iam list-user-policies --user-name $USER_NAME
   ```

### 问题 3: 凭证过期或失效

**症状：**
```bash
The security token included in the request is invalid
```

**解决方案：**

1. **检查 Access Key 状态：**
   - 登录 AWS Console
   - IAM → Users → Security credentials
   - 查看 Access Key 是否为 "Active"

2. **重新创建 Access Key：**
   - 删除旧的 Access Key
   - 创建新的 Access Key
   - 更新本地配置文件

### 问题 4: 多个账号混淆

**症状：**
操作了错误的 AWS 账号。

**解决方案：**

```bash
# 始终先确认当前账号
aws sts get-caller-identity

# 使用 profile 明确指定账号
aws s3 ls --profile sheldon2026

# 或设置环境变量
export AWS_PROFILE=sheldon2026
```

### 问题 5: Region 配置错误

**症状：**
找不到资源，但资源确实存在。

**原因：**
资源在不同的 region，但 CLI 使用了默认 region。

**解决方案：**

```bash
# 查看当前 region
aws configure get region

# 临时指定 region
aws ec2 describe-instances --region us-east-1

# 修改默认 region
aws configure set region ap-southeast-2

# 或在配置文件中设置
echo "region = ap-southeast-2" >> ~/.aws/config
```

---

## 安全最佳实践

### 1. Root 用户管理

#### ❌ 不要用 Root 用户做的事
- 创建 EC2、S3、RDS 等资源
- 日常开发和运维
- 给应用程序使用的 Access Keys
- 共享给团队成员

#### ✅ Root 用户只用于
- 修改账户设置（联系信息、支付方式）
- 关闭 AWS 账户
- 修改支持计划
- 恢复 IAM 权限（紧急情况）

#### ✅ Root 用户安全措施
- 启用 MFA（多因素认证）
- 删除所有 Access Keys
- 使用强密码
- 定期检查登录活动

### 2. IAM 用户管理

#### 最小权限原则

只授予完成任务所需的**最小权限**。

**不推荐：**
```
所有用户都给 AdministratorAccess
```

**推荐：**
```
开发人员 → PowerUserAccess（不能管理 IAM）
运维人员 → 特定服务的完全访问
只读用户 → ReadOnlyAccess
```

#### 使用用户组管理权限

**不推荐：**
```
给每个用户单独附加策略（难以维护）
```

**推荐：**
```
创建用户组（Developers、Admins、ReadOnly）
→ 给组附加策略
→ 用户加入组
→ 统一管理
```

### 3. Access Keys 管理

#### 创建 Access Keys

- ✅ 只在需要编程访问时创建
- ✅ 每个 IAM 用户最多 2 个 Access Keys
- ✅ 定期轮换（建议 90 天）

#### 保护 Access Keys

```bash
# ❌ 不要这样做
aws_access_key_id = "AKIA..."  # 硬编码在代码中
git add config.py              # 提交到 Git

# ✅ 应该这样做
# 使用环境变量
export AWS_ACCESS_KEY_ID=AKIA...

# 或使用配置文件
~/.aws/credentials

# 添加到 .gitignore
echo ".aws/" >> .gitignore
echo "*.csv" >> .gitignore
```

#### 检查 Access Keys 安全

```bash
# 查看 Access Key 创建时间
aws iam list-access-keys --user-name sheldon2026

# 输出示例
{
    "AccessKeyMetadata": [
        {
            "AccessKeyId": "AKIA4P4TR4HEWMFKDSGZ",
            "Status": "Active",
            "CreateDate": "2026-01-28T09:15:00+00:00"
        }
    ]
}
```

**如果超过 90 天，建议轮换：**

```bash
# 1. 创建新的 Access Key
aws iam create-access-key --user-name sheldon2026

# 2. 更新本地配置使用新 Key

# 3. 测试新 Key 是否工作
aws sts get-caller-identity

# 4. 删除旧 Key
aws iam delete-access-key --user-name sheldon2026 --access-key-id OLD_KEY_ID
```

### 4. MFA（多因素认证）

#### 为 IAM 用户启用 MFA

1. IAM → Users → sheldon2026 → Security credentials
2. Multi-factor authentication (MFA) → Assign MFA device
3. 选择虚拟 MFA 设备（如 Google Authenticator）
4. 扫描二维码并输入两个连续的 MFA 代码

#### CLI 使用 MFA

如果启用了 MFA，需要使用 STS 获取临时凭证：

```bash
# 获取临时凭证
aws sts get-session-token \
  --serial-number arn:aws:iam::858766041545:mfa/sheldon2026 \
  --token-code 123456

# 使用返回的临时凭证配置 CLI
```

### 5. 使用 IAM Roles（更安全）

对于 AWS 服务（如 EC2、Lambda），使用 **IAM Role** 而不是 Access Keys：

#### EC2 实例

```bash
# 不推荐：在 EC2 上配置 Access Keys
aws configure

# 推荐：给 EC2 附加 IAM Role
1. 创建 IAM Role
2. 附加所需策略
3. 启动 EC2 时指定 Instance Profile
4. EC2 自动获得临时凭证（无需配置）
```

#### Lambda 函数

```bash
# 创建 Lambda 时指定 Execution Role
# Lambda 自动使用该 Role 的权限
```

### 6. 监控和审计

#### CloudTrail

启用 CloudTrail 记录所有 API 调用：

```bash
# 创建 CloudTrail
aws cloudtrail create-trail \
  --name my-trail \
  --s3-bucket-name my-cloudtrail-bucket

# 启动记录
aws cloudtrail start-logging --name my-trail
```

#### 定期审计

```bash
# 查看所有 IAM 用户
aws iam list-users

# 查看所有 Access Keys
aws iam list-access-keys --user-name sheldon2026

# 查看 Access Key 最后使用时间
aws iam get-access-key-last-used --access-key-id AKIA...
```

### 7. 清理不用的资源

```bash
# 删除不用的 Access Keys
aws iam delete-access-key --user-name sheldon2026 --access-key-id AKIA...

# 删除不用的 IAM 用户
aws iam delete-user --user-name old-user

# 删除不用的策略
aws iam delete-policy --policy-arn arn:aws:iam::858766041545:policy/old-policy
```

---

## 快速参考命令

### 凭证配置

```bash
# 配置默认 profile
aws configure

# 配置指定 profile
aws configure --profile sheldon2026

# 查看配置
aws configure list

# 查看所有 profiles
cat ~/.aws/credentials | grep "\["
```

### 身份验证

```bash
# 验证当前身份
aws sts get-caller-identity

# 获取账户 ID
aws sts get-caller-identity --query Account --output text

# 获取当前用户名
aws iam get-user --query User.UserName --output text
```

### 权限检查

```bash
# 用户直接权限
aws iam list-attached-user-policies --user-name USERNAME
aws iam list-user-policies --user-name USERNAME

# 用户组权限
aws iam list-groups-for-user --user-name USERNAME
aws iam list-attached-group-policies --group-name GROUPNAME

# 测试服务访问
aws ec2 describe-regions        # 测试 EC2
aws s3 ls                        # 测试 S3
aws iam list-users               # 测试 IAM
```

### Access Key 管理

```bash
# 列出 Access Keys
aws iam list-access-keys --user-name USERNAME

# 创建 Access Key
aws iam create-access-key --user-name USERNAME

# 停用 Access Key
aws iam update-access-key --user-name USERNAME \
  --access-key-id KEY_ID --status Inactive

# 删除 Access Key
aws iam delete-access-key --user-name USERNAME \
  --access-key-id KEY_ID

# 查看最后使用时间
aws iam get-access-key-last-used --access-key-id KEY_ID
```

### 环境变量

```bash
# 查看 AWS 相关环境变量
env | grep AWS

# 清除环境变量
unset AWS_PROFILE
unset AWS_DEFAULT_PROFILE
unset AWS_ACCESS_KEY_ID
unset AWS_SECRET_ACCESS_KEY

# 设置环境变量
export AWS_PROFILE=sheldon2026
export AWS_DEFAULT_REGION=ap-southeast-2
```

---

## 附录

### 账号信息

- **账号 ID**: `858766041545`（显示为 `8587-6604-1545`）
- **账号名**: `xiaodongyan`
- **默认 Region**: `ap-southeast-2` (Sydney)

### IAM 用户信息

- **用户名**: `sheldon2026`
- **User ID**: `AIDA4P4TR4HES6FX4APQK`
- **ARN**: `arn:aws:iam::858766041545:user/sheldon2026`
- **创建时间**: 2026-01-28

### 权限配置

- **用户组**: `knowledgedemo`
- **组策略**: `AdministratorAccess`
- **直接附加**: `IAMUserChangePassword`

### Access Key

- **Access Key ID**: `<your-access-key-id>`
- **创建时间**: 2026-01-28
- **状态**: Active
- **用途**: Local development CLI

### 参考链接

- [AWS IAM 文档](https://docs.aws.amazon.com/IAM/latest/UserGuide/)
- [AWS CLI 配置](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html)
- [IAM 最佳实践](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [AWS Security Best Practices](https://aws.amazon.com/architecture/security-identity-compliance/)

---

**文档版本**: 1.0
**最后更新**: 2026-01-28
**维护者**: Sheldon
