# iOS Quiz Submission Implementation

这个文档说明了如何在iOS应用中实现测验提交功能，对应后端的submission API。

## 功能概述

该实现提供了完整的测验提交流程：

1. **数据模型转换**: 将本地存储的用户答案转换为API需要的格式
2. **网络请求**: 通过RESTful API将答案提交到服务器
3. **错误处理**: 完善的错误处理和用户反馈
4. **状态管理**: UI状态同步和加载指示器

## 关键组件

### 1. 数据模型 (Quiz.swift)

#### 提交答案模型
```swift
enum AnyAnswer: Codable, Equatable {
    case multipleChoice(MultipleChoiceAnswer)
    case fillInTheBlank(FillInTheBlankAnswer) 
    case calculation(CalculationAnswer)
}

struct MultipleChoiceAnswer: Codable, Equatable {
    let selectedOption: Int
}

struct FillInTheBlankAnswer: Codable, Equatable {
    let textAnswer: String
}

struct CalculationAnswer: Codable, Equatable {
    let numericAnswer: String
}
```

#### 提交请求和响应
```swift
struct QuizSubmissionRequest: Codable {
    let answers: [ClientAnswerInput]
}

struct QuizSubmissionResponse: Codable {
    let attemptId: UUID
    let message: String
}
```

### 2. 网络端点 (Quiz.swift)

```swift
struct QuizSubmissionEndpoint: Endpoint {
    let submissionId: UUID
    let submissionRequest: QuizSubmissionRequest
    
    var path: String { "/submissions/\(submissionId)" }
    var method: HTTPMethod { .POST }
    var body: RequestBody? { .json(submissionRequest) }
    var requiredAuth: Bool { true }
}
```

### 3. 提交逻辑 (QuizViewModel.swift)

#### 主要提交方法
```swift
func submitQuiz() async {
    // 1. 验证测验状态
    // 2. 构建提交数据
    // 3. 发送到服务器
    // 4. 处理响应和错误
}
```

#### 答案构建方法
```swift
internal func buildSubmissionAnswers(from attempt: QuizAttempt) -> [ClientAnswerInput] {
    // 将本地存储的答案转换为API格式
}
```

## API 对应关系

| 后端模型 | iOS模型 | 说明 |
|---------|--------|------|
| `QuizSubmissionRequest` | `QuizSubmissionRequest` | 提交请求结构体 |
| `ClientAnswerInput` | `ClientAnswerInput` | 单个答案输入 |
| `MultipleChoiceAnswer` | `MultipleChoiceAnswer` | 多选题答案 |
| `FillInTheBlankAnswer` | `FillInTheBlankAnswer` | 填空题答案 |
| `CalculationAnswer` | `CalculationAnswer` | 计算题答案 |

## 使用流程

### 1. 测验完成时
当用户完成所有问题后，`QuizCompletionView`会显示提交按钮：

```swift
Button(action: {
    Task {
        await viewModel.submitQuiz()
    }
}) {
    // 带加载状态的按钮UI
}
```

### 2. 答案收集
系统自动收集用户已提交的答案：

```swift
let answers = buildSubmissionAnswers(from: attempt)
```

### 3. 网络提交
通过配置的端点提交到服务器：

```swift
let endpoint = QuizSubmissionEndpoint(
    submissionId: submissionId,
    submissionRequest: request
)
```

### 4. 状态管理
- 提交中: 显示加载指示器
- 成功: 保存到本地数据库
- 失败: 显示错误信息，恢复状态

## 错误处理

### 网络错误
- 连接失败
- 服务器错误 (5xx)
- 客户端错误 (4xx) 
- 认证失败 (401)

### 数据错误
- 答案格式不正确
- 必需字段缺失
- 数据序列化失败

### UI反馈
```swift
.alert(item: $viewModel.alertItem) { alertItem in
    Alert(
        title: Text(alertItem.title),
        message: Text(alertItem.message),
        dismissButton: .default(Text("确定"))
    )
}
```

## 测试

### 单元测试
```swift
@Test("Test building submission answers from QuizAttempt")
func testBuildSubmissionAnswers() async throws {
    // 测试答案构建逻辑
}

@Test("Test QuizSubmissionRequest JSON encoding")  
func testSubmissionRequestEncoding() async throws {
    // 测试JSON序列化
}
```

### Mock网络服务
```swift
func configureMockSubmission() {
    self.mockResponse = QuizSubmissionResponse(
        attemptId: UUID(),
        message: "Your answers have been submitted and are pending grading"
    )
}
```

## 后端兼容性

该实现完全兼容提供的后端API：

- **端点**: `POST /submissions/{submission_id}`
- **认证**: Bearer Token
- **状态码**: 202 (Accepted)
- **错误处理**: 404, 403, 409, 500

## 安全考虑

1. **认证**: 所有请求都需要有效的Bearer token
2. **权限验证**: 只有测验所有者可以提交答案
3. **状态检查**: 只能提交进行中的测验
4. **数据验证**: 客户端和服务器都进行数据验证

## 未来改进

1. **离线支持**: 网络不可用时缓存提交请求
2. **重试机制**: 失败时自动重试
3. **分批提交**: 大量答案时分批发送
4. **实时反馈**: WebSocket或推送通知显示评分结果

## 故障排除

### 常见问题

1. **Token过期**: 自动重新登录
2. **网络超时**: 显示重试选项
3. **数据不一致**: 重新同步本地状态
4. **服务器维护**: 显示友好的维护提示

### 调试信息
启用详细日志记录来追踪问题：
```swift
print("✅ 测验提交成功: \(response.message)")
print("❌ 保存到本地失败: \(error)")
```