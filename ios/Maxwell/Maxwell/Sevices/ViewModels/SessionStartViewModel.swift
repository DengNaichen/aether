import Foundation
import Combine

// 假设 AlertItem 和 NetworkServicing 已经定义

class SessionStartViewModel: ObservableObject {
    
    private let network: NetworkServicing
    
    @Published var isLoading: Bool = false
    @Published var sessionResponse: SessionStartResponse? = nil // 对应 SessionStartResponse 模型
    @Published var alartItem: AlertItem?
    
    
    init(network: NetworkServicing) {
        self.network = network
    }
    
    /// 根据课程ID和问题数量，开始一个新的学习会话
    func startSession(courseId: String, questionCount: Int) async {
        // 1. 设置初始状态
        isLoading = true
        defer { isLoading = false } // 确保函数退出时，加载状态恢复为 false
        alartItem = nil
        sessionResponse = nil
        
        do {
            // 2. 准备并发送网络请求
            let requestData = SessionStartRequest(courseId: courseId)
            let sessionEndpoint = SessionStartEndpoint(startSessionRequest: requestData)
            
            let response: SessionStartResponse = try await network.request(
                endpoint: sessionEndpoint,
                responseType: SessionStartResponse.self
            )
            
            // 3. 处理成功响应
            // 在主线程上更新 @Published 属性
            await MainActor.run {
                self.sessionResponse = response
            }
            
        } catch {
            // 4. 处理各种错误
            let errorMessage: String
            if let networkError = error as? NetworkError {
                errorMessage = networkError.message
            } else {
                errorMessage = "An unknown error happen: \(error.localizedDescription)"
            }
            
            // 在主线程上更新 @Published 属性
            await MainActor.run {
                alartItem = AlertItem(title: "Session Start Failed",
                                      message: errorMessage)
            }
        }
    }
}
