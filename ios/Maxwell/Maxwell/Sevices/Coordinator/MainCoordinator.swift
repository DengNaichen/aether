import Foundation
import Combine
import SwiftUI

enum MainState {
    case dashboard
    case inQuiz(sessionData: SessionStartResponse)
    case inEnroll
}

@MainActor
class MainCoordinator: ObservableObject {
    
    var dashboardViewModel: DashboardViewModel

    private let networkService: NetworkService
    var onLogout: () -> Void
    
    init(networkService: NetworkService, onLogout: @escaping () -> Void) {
        self.networkService = networkService
        self.onLogout = onLogout
        // TODO: Do I need the onLogout here ??
        self.dashboardViewModel = DashboardViewModel(network: networkService)
    }

}
    
//    func enrollInDefaultCourse() async {
//        // TODO: create the dashboard view model
//        await dashboardViewModel.enrollInCourse(courseId: "g11_phys")
//    }
//    
//    func startQuizSession() async {
//        do {
//            // 1. 调用 ViewModel 来执行业务逻辑
//            print("Coordinator: Attempting to start session...")
//            let sessionData = try await dashboardViewModel.startSession(courseId: "g11_phys", questionCount: 5)
//            
//            // 2.【验证步骤】将成功获取的数据打印到控制台
//            //   这可以证明你的 View -> Coordinator -> ViewModel -> NetworkService 调用链是通的！
//            print("✅ Refactoring successful! Fetched session data: \(sessionData)")
//            
//            
//            // TODO: Implement navigation to QuizView once ready.
//            // self.state = .inQuiz(sessionData: sessionData)
//            
//        } catch {
//            // 错误处理逻辑仍然非常重要
//            dashboardViewModel.handleError(error, title: "Session Start Failed")
//        }
//    }
//}

