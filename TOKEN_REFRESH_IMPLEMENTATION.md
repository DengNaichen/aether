# Token 刷新功能实现总结

## 📊 实施概览

本文档总结了使用 **TDD (Test-Driven Development)** 方法实现的 Token 刷新功能。

**实施日期:** 2025-10-25
**方法:** 测试驱动开发 (TDD)
**选择方案:** 选项 A - 同时返回新的 `access_token` 和 `refresh_token`（Token 轮换策略）

---

## ✅ 已完成的工作

### **后端实现**

#### 1. 测试文件创建
**文件:** `tests/test_token_refresh.py`

**测试用例:**
- ✅ `test_refresh_token_returns_both_tokens` - 验证返回两个 token
- ✅ `test_refresh_token_invalidates_old_token` - 验证旧 token 失效
- ✅ `test_refresh_token_with_invalid_token` - 验证无效 token 被拒绝
- ✅ `test_refresh_token_with_expired_token` - 验证过期 token 被拒绝
- ✅ `test_refresh_token_saves_new_token_to_db` - 验证新 token 保存到数据库
- ✅ `test_refresh_token_with_nonexistent_user` - 验证不存在用户的 token 被拒绝

#### 2. 功能实现
**文件:** `app/routes/user.py`

**改动:**
```python
# 第 89 行 - 改变返回类型
@router.post("/refresh", response_model=Token)  # 原本是 AccessToken

# 第 143-147 行 - 返回两个 token
return {
    "access_token": new_access_token,
    "refresh_token": new_refresh_token,  # 新增
    "token_type": "bearer"
}
```

**效果:**
- 用户刷新 token 时，同时获得新的 `access_token` 和 `refresh_token`
- 旧的 `refresh_token` 自动失效（被新 token 替换）
- 实现了 Token 轮换安全策略

---

### **iOS端实现**

#### 1. 测试文件创建
**文件:** `ios/Aether/AetherTests/TokenRefreshTests.swift`

**使用框架:** Swift Testing（`@Test` 和 `#expect`）

**测试用例:**
- ✅ `refreshTokenEndpointHasCorrectPath` - 验证端点路径
- ✅ `refreshTokenEndpointUsesPostMethod` - 验证 HTTP 方法
- ✅ `refreshTokenEndpointDoesNotRequireAuth` - 验证不需要认证头
- ✅ `refreshTokenRequestEncodesToSnakeCase` - 验证 JSON 编码格式
- ✅ `authServiceRefreshTokensReturnsTrueOnSuccess` - 验证刷新成功
- ✅ `authServiceRefreshTokensReturnsFalseWhenNoRefreshToken` - 验证无 token 处理
- ✅ `authServiceRefreshTokensThrowsErrorOnNetworkFailure` - 验证网络错误处理
- 🟡 `networkService401TriggersTokenRefreshAndRetry` - 占位符（需更复杂的 mock）
- 🟡 `networkServiceLogsOutWhenRefreshFails` - 占位符（需 spy 模式）
- 🟡 `networkServiceDoesNotRetryInfinitely` - 占位符（需 spy 模式）

#### 2. 数据模型
**文件:** `ios/Aether/Aether/Models/User.swift`

**新增:**
```swift
struct RefreshTokenRequest: Encodable {
    let refreshToken: String

    enum CodingKeys: String, CodingKey {
        case refreshToken = "refresh_token"
    }
}
```

#### 3. 网络端点
**文件:** `ios/Aether/Aether/Models/Endpoint.swift`

**新增:**
```swift
struct RefreshTokenEndpoint: Endpoint {
    let refreshToken: String

    var path: String { "/users/refresh" }
    var method: HTTPMethod { .POST }
    var body: RequestBody? {
        .json(RefreshTokenRequest(refreshToken: refreshToken))
    }
    var requiredAuth: Bool { false }
}
```

**位置:** [Endpoint.swift:97-106](ios/Aether/Aether/Models/Endpoint.swift#L97-L106)

#### 4. AuthService 刷新方法
**文件:** `ios/Aether/Aether/ViewModels/Auth/AuthService.swift`

**新增方法:**
```swift
func refreshTokens(networkService: NetworkServicing) async throws -> Bool
```

**功能:**
- 检查是否有 refresh token
- 调用刷新端点
- 保存新的 tokens 到 KeyChain
- 返回成功/失败状态

**位置:** [AuthService.swift:43-70](ios/Aether/Aether/ViewModels/Auth/AuthService.swift#L43-L70)

#### 5. NetworkService 401 自动刷新
**文件:** `ios/Aether/Aether/ViewModels/Network/NetworkServicing.swift`

**改动 1: 方法签名**
```swift
func request<T: Decodable>(
    endpoint: Endpoint,
    responseType: T.Type,
    isRetry: Bool = false  // 新增参数
) async throws -> T
```

**改动 2: 401 处理逻辑**
```swift
case 401:
    // 如果已经是重试，直接登出（防止无限循环）
    if isRetry {
        authService.logout()
        throw NetworkError.tokenNotFound
    }

    // 尝试刷新 token
    do {
        let refreshSuccess = try await authService.refreshTokens(networkService: self)

        if refreshSuccess {
            // 刷新成功，重试原请求
            return try await request(
                endpoint: endpoint,
                responseType: responseType,
                isRetry: true  // 标记为重试
            )
        } else {
            // 刷新失败，登出
            authService.logout()
            throw NetworkError.tokenNotFound
        }
    } catch {
        // 刷新过程出错，登出
        authService.logout()
        throw NetworkError.tokenNotFound
    }
```

**位置:** [NetworkServicing.swift:89-130](ios/Aether/Aether/ViewModels/Network/NetworkServicing.swift#L89-L130)

**特性:**
- ✅ 收到 401 时自动尝试刷新 token
- ✅ 刷新成功后自动重试原请求
- ✅ 刷新失败时登出用户
- ✅ 防止无限重试循环（最多重试 1 次）
- ✅ 详细的日志输出

---

## 📂 修改的文件清单

### 后端（2个文件）
1. `tests/test_token_refresh.py` - **新建**
2. `app/routes/user.py` - **修改** 2 处

### iOS端（5个文件）
1. `ios/Aether/AetherTests/TokenRefreshTests.swift` - **新建**
2. `ios/Aether/Aether/Models/User.swift` - **修改** 添加 RefreshTokenRequest
3. `ios/Aether/Aether/Models/Endpoint.swift` - **修改** 添加 RefreshTokenEndpoint
4. `ios/Aether/Aether/ViewModels/Auth/AuthService.swift` - **修改** 添加 refreshTokens 方法
5. `ios/Aether/Aether/ViewModels/Network/NetworkServicing.swift` - **修改** 添加 isRetry 参数和 401 处理逻辑

---

## 🧪 如何测试

### 后端测试

```bash
# 运行所有 token refresh 测试
pytest tests/test_token_refresh.py -v

# 运行单个测试
pytest tests/test_token_refresh.py::TestTokenRefresh::test_refresh_token_returns_both_tokens -v

# 运行测试并查看覆盖率
pytest tests/test_token_refresh.py --cov=app/routes/user --cov-report=term-missing
```

### iOS端测试

1. **在 Xcode 中运行测试:**
   - 打开 Xcode
   - `Cmd + U` 运行所有测试
   - 或者选择 `Product > Test`

2. **运行特定测试套件:**
   - 在 Test Navigator 中选择 `TokenRefreshTests`
   - 右键点击 → `Run "TokenRefreshTests"`

3. **查看测试覆盖率:**
   - `Product > Scheme > Edit Scheme`
   - 选择 `Test` 标签页
   - 勾选 `Code Coverage`
   - 运行测试后在 Report Navigator 查看覆盖率

### 手动测试

#### 测试自动刷新功能

1. **登录应用**
2. **等待 access token 过期**（或在后端手动设置较短的过期时间）
3. **执行任何需要认证的操作**（如获取课程列表）
4. **观察日志输出:**
   ```
   ⚠️ [NetworkService] Received 401 Unauthorized
   🔄 [NetworkService] Attempting to refresh token...
   🔄 [AuthService] Refreshing tokens...
   ✅ [AuthService] Tokens refreshed successfully
   ✅ [NetworkService] Token refreshed, retrying original request
   ```
5. **验证操作成功完成**，用户无感知

#### 测试刷新失败场景

1. **删除后端数据库中的 refresh_token**
2. **触发需要认证的操作**
3. **观察日志:**
   ```
   ⚠️ [NetworkService] Received 401 Unauthorized
   🔄 [NetworkService] Attempting to refresh token...
   ❌ [NetworkService] Token refresh failed: ..., logging out
   ```
4. **验证用户被登出**

---

## 🔒 安全特性

### Token 轮换策略
- ✅ 每次刷新都生成新的 `refresh_token`
- ✅ 旧的 `refresh_token` 立即失效
- ✅ 防止 token 被盗用后长期有效

### 防止无限循环
- ✅ `isRetry` 标志确保最多重试 1 次
- ✅ 避免刷新端点本身返回 401 导致的死循环

### 失败安全
- ✅ 任何刷新失败都会登出用户
- ✅ 清除本地 token 数据
- ✅ 防止无效状态

---

## 📈 性能考虑

### 优点
- ✅ 用户无感知的 token 刷新
- ✅ 减少重新登录的次数
- ✅ 改善用户体验

### 注意事项
- ⚠️ 刷新操作会增加一次网络请求
- ⚠️ 原请求会被重试，总共发送 3 次请求（原请求 → 刷新 → 重试）
- 💡 **未来优化:** 可以在 token 即将过期前主动刷新，避免 401

---

## 🚀 后续优化建议

### 1. 主动刷新（推荐）
在 token 即将过期前自动刷新，避免等待 401 错误。

**实现思路:**
- 解析 JWT 获取过期时间
- 在过期前 5 分钟自动刷新
- 后台定时任务检查

### 2. 刷新队列
多个请求同时收到 401 时，只刷新一次，其他请求等待。

**实现思路:**
- 使用锁或信号量
- 第一个请求刷新，其他请求等待
- 刷新完成后所有请求重试

### 3. 离线支持
结合离线队列，网络恢复时自动刷新并重试。

**实现思路:**
- 检测网络状态
- 离线时将请求加入队列
- 网络恢复时刷新 token 并重试队列

### 4. 更详细的日志
记录刷新频率、失败原因等，用于监控和调试。

---

## ✅ 验收标准

### 后端
- [x] `/users/refresh` 端点返回 `access_token` 和 `refresh_token`
- [ ] 所有测试用例通过（需在正确的环境中运行）
- [x] 旧 `refresh_token` 失效
- [x] 新 `refresh_token` 保存到数据库

### iOS端
- [x] `RefreshTokenEndpoint` 正确定义
- [x] `RefreshTokenRequest` 正确编码
- [x] `AuthService.refreshTokens()` 实现
- [x] `NetworkService` 401 自动刷新
- [x] 防止无限重试
- [ ] 所有测试用例通过（需在 Xcode 中运行）

### 集成测试
- [ ] 用户可以完整使用 app 而无需频繁重新登录
- [ ] Token 过期时自动刷新（用户无感知）
- [ ] 刷新失败时正确登出
- [ ] 日志输出清晰

---

## 📚 相关文档

- [ROADMAP.md](ROADMAP.md) - 完整开发路线图
- [FastAPI OAuth2 文档](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)
- [RFC 6749 - OAuth 2.0](https://datatracker.ietf.org/doc/html/rfc6749)
- [Swift Testing 文档](https://developer.apple.com/documentation/testing)

---

## 🎉 总结

Token 刷新功能已完整实现，采用 TDD 方法确保代码质量。主要特性包括：

1. ✅ **Token 轮换策略** - 每次刷新都更新 refresh token，提高安全性
2. ✅ **自动重试** - 401 错误时自动刷新并重试，用户无感知
3. ✅ **防止循环** - `isRetry` 标志确保最多重试 1 次
4. ✅ **失败安全** - 刷新失败时清晰地登出用户
5. ✅ **详细日志** - 便于调试和监控

**下一步:** 运行测试验证所有功能正常工作，然后考虑实施优化建议。
