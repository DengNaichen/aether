
# SwiftUI 并发重构指南：彻底告别 Main Actor 问题

本文档旨在提供一个清晰、可操作的指南, 帮助你将项目重构为现代、健壮且线程安全的 Swift 并发模型. 遵循本指南将系统性地解决在 SwiftUI 中常见的 "Main Actor" 警告和崩溃.

## 核心原则: UI 状态属于 Main Actor

在重构之前, 理解一个核心原则至关重要: **任何直接驱动 UI 变化的类, 都必须被主线程 (Main Actor) 所拥有和保护.**

在你的项目中, `AetherApp` 的顶层视图依赖于 `authService.isAuthenticated` 来决定显示登录页还是主页. 这意味着 `AuthService` 不仅仅是一个后台服务, 它还是一个 **UI 状态控制器**.

因此, 我们必须将其标记为 `@MainActor`. 这保证了它的 `@Published` 属性总是在主线程上被修改, 从根本上解决了当后台线程 (如 token 刷新失败时) 尝试修改 UI 状态而引发的冲突.

```swift
@MainActor // <-- 关键修复: 声明这个类属于 UI 主岛
class AuthService: ObservableObject {
    @Published private(set) var isAuthenticated: Bool = false
    // ...
}
```

## 心智模型: "UI主岛" 与 "工作岛"

为了简化理解, 我们可以使用一个比喻:

- **`@MainActor` 是 "UI主岛"**: 这是一个特殊的岛屿, 所有 UI 工作都在这里进行. 岛上规定**同一时间只能有一个工人在工作** (主线程), 以免混乱.
  - **你的所有 `View` 和 `ObservableObject` (ViewModel, AuthService) 都应该住在这个岛上.**

- **后台线程是 "工作岛"**: 网络请求等耗时操作都在不同的"工作岛"上进行, 这样"UI主岛"就不会被卡住.

- **`async / await` 是 "派单与等待"**:
  - 当 "UI主岛" 上的代码执行到 `await network.request()` 时, 它会把这个耗时的活儿**派单**给一个"工作岛".
  - 然后, "UI主岛" 的工人就解放了, 可以继续响应用户操作, UI 保持流畅. 他只需要在原地**等待**工作岛的结果.
  - 当"工作岛"完成后, 结果会自动送回"UI主岛", `await` 后面的代码会**自动在主线程上继续执行**.

---

## 重构实战四条军规

遵循以下四条简单的规则, 可以系统性地解决所有并发问题.

### 军规一: 驱动 UI 的类, 必须住在"UI主岛"

- **识别**: 任何 `class` 只要是 `ObservableObject`, 并且其 `@Published` 属性被 `View` 直接或间接使用.
- **行动**: 在 `class` 声明前加上 `@MainActor`.
- **示例**:
  ```swift
  @MainActor
  class CourseViewModel: ObservableObject {
      @Published var courses: [Course] = []
      // ...
  }
  ```

### 军规二: 耗时的任务, 都要能"派单"

- **识别**: 任何需要网络请求、大量计算、读写文件的函数.
- **行动**: 在函数签名上加上 `async`. 如果可能失败, 再加上 `throws`.
- **示例**:
  ```swift
  // 在 ViewModel 中
  func fetchCourses() async throws {
      // ...
  }
  ```

### 军规三: 调用"派单"任务, 必须"等待"

- **识别**: 在一个 `async` 函数内部, 调用另一个 `async` 函数.
- **行动**: 在调用前加上 `await`. 如果它会 `throws`, 就用 `try await`.
- **示例**:
  ```swift
  // 在 async func fetchCourses() 内部
  let endpoint = AllCoursesEndpoint()
  let response = try await network.request(endpoint: endpoint, responseType: FetchAllCoursesResponse.self)
  self.courses = response.courses
  ```

### 军规四: 从 `View` 发起"派单", 要用 `.task`

- **识别**: 当 `View` **出现时**需要加载数据, 或者**点击按钮**执行一个耗时操作.
- **行动**:
    1.  对于 `View` 出现时加载: 使用 `.task` 修饰符.
    2.  对于按钮点击: 在 `action` 闭包中包裹一层 `Task { ... }`.
- **示例**:

  **1. View 出现时加载:**
  ```swift
  struct CourseView: View {
      @StateObject var viewModel: CourseViewModel

      var body: some View {
          List(viewModel.courses) { course in
              Text(course.courseName)
          }
          .task { // <-- 在这里发起任务
              do {
                  try await viewModel.fetchCourses()
              } catch {
                  // 处理错误
              }
          }
      }
  }
  ```

  **2. 按钮点击:**
  ```swift
  Button("Login") {
      Task { // <-- 在这里发起任务
          await loginViewModel.login(email: email, password: password)
      }
  }
  ```

---

## 你的重构清单

- [ ] **审查 `ObservableObject`**: 检查项目中所有的 `ObservableObject` 类 (`AuthService`, `CourseViewModel`, `DashboardViewModel` 等), 为它们统一添加 `@MainActor` 标记.

- [ ] **改造 ViewModel 方法**: 找到所有执行网络请求的 ViewModel 方法.
  - 将它们的方法签名改为 `async` 或 `async throws`.
  - 移除旧的基于闭包 (completion handler) 或 Combine (`.sink`, `cancellables`) 的代码.
  - 使用 `try await` 来调用 `network.request`.

- [ ] **更新 View**: 检查所有 `View`.
  - 将 `.onAppear { viewModel.fetchData() }` 的写法替换为 `.task { await viewModel.fetchData() }`.
  - 确保按钮触发的异步操作被包裹在 `Task { ... }` 中.

- [ ] **(推荐) 统一依赖**: 仿照 `LoginViewModelRefactored` 的设计, 让所有需要认证状态或操作的 ViewModel 都依赖 `AuthService`, 而不是直接调用 `TokenManager.shared`.

- [ ] **(可选) 清理代码**: 在确认 `AuthService` 等类已标记为 `@MainActor` 后, 可以移除 `NetworkService` 中手动的 `await MainActor.run { ... }` 代码块, 直接调用 `authService.logout()`, 使代码更简洁.
