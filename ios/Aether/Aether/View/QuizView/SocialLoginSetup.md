# 社交登录配置指南

## Apple Sign-In 配置

### 1. Xcode项目配置
1. 在Xcode中选择项目 > Target > Signing & Capabilities
2. 点击 "+ Capability" 添加 "Sign in with Apple"
3. 确保Bundle Identifier正确配置

### 2. Apple Developer Portal配置
1. 登录 [Apple Developer Portal](https://developer.apple.com)
2. 前往 Certificates, Identifiers & Profiles
3. 选择你的App ID，确保"Sign In with Apple"服务已启用

### 3. 后端API端点
确保后端提供以下端点：
```
POST /auth/apple
Content-Type: application/json

{
    "user_id": "string",
    "identity_token": "string", 
    "email": "string",
    "first_name": "string",
    "last_name": "string"
}
```

## Google Sign-In 配置

### 1. 添加依赖
在您的 `Package.swift` 或通过 Xcode Package Manager 添加：
```
https://github.com/google/GoogleSignIn-iOS
```

### 2. Google Cloud Console配置
1. 前往 [Google Cloud Console](https://console.cloud.google.com)
2. 创建新项目或选择现有项目
3. 启用 Google Sign-In API
4. 创建 OAuth 2.0 客户端 ID (iOS类型)
5. 设置Bundle ID为您的应用Bundle ID

### 3. 下载配置文件
1. 下载 `GoogleService-Info.plist` 文件
2. 将文件拖入Xcode项目中
3. 确保文件已添加到项目Target

### 4. URL Scheme配置
1. 在Xcode中选择项目 > Target > Info
2. 展开 "URL Types"
3. 添加新的URL Scheme，值为 `GoogleService-Info.plist` 中的 `REVERSED_CLIENT_ID`

### 5. 后端API端点
确保后端提供以下端点：
```
POST /auth/google
Content-Type: application/json

{
    "user_id": "string",
    "id_token": "string",
    "email": "string", 
    "first_name": "string",
    "last_name": "string"
}
```

## 注意事项

### Apple Sign-In
- Apple Sign-In在模拟器上可能无法正常工作，建议在真机上测试
- 用户可能选择隐藏邮箱地址，需要处理空邮箱的情况
- Identity token需要在后端验证其有效性

### Google Sign-In
- 确保Google Sign-In配置正确，否则会返回错误
- ID token需要在后端验证
- 测试时注意网络连接

### 通用
- 两种登录方式都需要适当的错误处理
- 考虑添加重试机制
- 确保UI在加载时正确显示加载状态

## 测试建议

1. **Apple Sign-In测试**
   - 在真机上测试完整流程
   - 测试用户拒绝授权的情况
   - 测试用户选择隐藏邮箱的情况

2. **Google Sign-In测试**
   - 测试网络异常情况
   - 测试用户取消登录的情况
   - 验证token在后端的处理

3. **通用测试**
   - 测试后端API的错误响应处理
   - 测试网络超时情况
   - 确保用户体验流畅