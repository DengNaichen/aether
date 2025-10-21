# 移除 Coordinator 模式重构计划

## 1. 目标

本项目旨在使用 SwiftUI 原生的状态管理和导航功能，完全替代当前项目中使用的 Coordinator 模式。这将简化代码结构，减少样板代码，并使导航逻辑更符合 SwiftUI 的声明式范式。

## 2. 分析结论

当前项目中的三层 Coordinator 结构（`AppCoordinator`, `OnboardingCoordinator`, `MainCoordinator`）对于应用目前的线性导航需求来说过于复杂。SwiftUI 的内置功能足以处理认证状态切换和视图导航，无需引入额外的抽象层。

## 3. 重构步骤

---

### **第一步：修改应用入口 `MaxwellApp.swift`**

**目标**: 将应用的根视图决策逻辑从 `AppCoordinatorView` 移至 `MaxwellApp.swift`。

1.  **读取 `MaxwellApp.swift`**: 获取当前文件内容以进行修改。
2.  **修改 `MaxwellApp.swift`**:
    *   创建并持有 `AuthService` 和 `NetworkService` 的 `@StateObject` 实例。
    *   在 `WindowGroup` 的 `body` 中，使用 `if authService.isAuthenticated` 条件来决定显示 `MainTabView` 还是 `LoginView`。
    *   通过 `.environmentObject()` 将 `authService` 和 `networkService` 注入到视图层级中。

---

### **第二步：简化认证流程（移除 `OnboardingCoordinator`）**

**目标**: 移除 `OnboardingCoordinator`，让 `LoginView` 和 `RegistrationView` 直接管理它们之间的切换。

1.  **修改 `LoginViewModel` 和 `RegistrationViewModel`**:
    *   移除构造函数中的 `onLoginSuccess` 和 `onRegisterSuccess` 闭包。
    *   在登录/注册成功后，直接调用注入的 `AuthService` 实例来更新认证状态。
2.  **修改 `LoginView`**:
    *   添加一个 `@State private var isShowingRegistration = false` 变量。
    *   当用户点击“注册”按钮时，将 `isShowingRegistration` 设置为 `true`。
    *   使用 `.sheet(isPresented: $isShowingRegistration)` 来模态显示 `RegistrationView`。

---

### **第三步：简化主应用导航（移除 `MainCoordinator`）**

**目标**: 移除 `MainCoordinator`，为未来的导航需求准备好 `NavigationStack`。

1.  **确认主视图**: 确认 `MainTabView` 是用户登录后看到的主界面。
2.  **准备导航**:
    *   在 `DashboardView` 或其他需要层级导航的视图中，将其内容包裹在 `NavigationStack` 中。
    *   `DashboardViewModel` 将不再由 Coordinator 创建，而是在 `DashboardView` 内部通过 `@StateObject` 直接初始化。

---

### **第四步：清理项目文件**

**目标**: 删除所有不再需要的 Coordinator 相关文件。

1.  **删除视图文件**:
    *   `Maxwell/View/CoordinatorView/AppCoordinatorView.swift`
    *   `Maxwell/View/CoordinatorView/OnboardingCoordinatorView.swift`
    *   `Maxwell/View/CoordinatorView/MainCoordinatorView.swift`
    *   删除 `Maxwell/View/CoordinatorView/` 目录。
2.  **删除视图模型文件**:
    *   `Maxwell/ViewModels/Coordinator/AppCoordinator.swift`
    *   `Maxwell/ViewModels/Coordinator/OnboardingCoordinator.swift`
    *   `Maxwell/ViewModels/Coordinator/MainCoordinator.swift`
    *   删除 `Maxwell/ViewModels/Coordinator/` 目录。
