import SwiftUI
//import SwiftData

@main
struct MaxwellApp: App {
    private var networkService: NetworkService

        // 自定义 App 的构造器来初始化网络服务
        init() {
            // ⚠️ 把这里的 IP 地址换成你自己的！
            let ipAddress = "192.168.2.13"
            
            guard let baseURL = URL(string: "http://\(ipAddress):8000") else {
                // 如果 URL 无效，这是一个致命错误，直接让 App 崩溃以便在开发时发现
                fatalError("Invalid base URL provided.")
            }
            
            // 使用 baseURL 初始化 NetworkService
            self.networkService = NetworkService(baseURL: baseURL)
        }
        
        var body: some Scene {
            WindowGroup {
                // 用 networkService 实例创建 ViewModel
                let registrationViewModel = RegistrationViewModel(network: networkService)
                
                // 将 ViewModel 注入到视图中
                RegistrationView(viewModel: registrationViewModel)
            }
        }
    
}
