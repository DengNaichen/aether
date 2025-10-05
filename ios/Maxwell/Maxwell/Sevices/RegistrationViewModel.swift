import SwiftUI
import Foundation
import Combine


class RegistrationViewModel: ObservableObject {
    @Published var name: String = ""
    @Published var email: String = ""
    @Published var password: String = ""
    
    @Published var showAlert: Bool = false
    @Published var alertMessage: String = ""
    
    func registerUser() {
        guard let url = URL(string: "http://127.0.0.1:8000/register") else {
            print("Invalid URL")
            return
        }
        
        let registrationData = RegistrationRequest(name: name, email: email, password: password)
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        do {
            let jsonData = try JSONEncoder().encode(registrationData)
            request.httpBody = jsonData
        } catch {
            DispatchQueue.main.async {
                self.alertMessage = "Cannot prepare data, please try again later"
                self.showAlert = true
            }
            return
        }
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            DispatchQueue.main.async {
                if let error = error {
                    
                    print("--- NETWORK ERROR ---")
                    print(error.localizedDescription)

                    self.alertMessage = "Network Error: \(error.localizedDescription)"
                    self.showAlert = true
                    return
                }
                
                guard let httpResponse = response as? HTTPURLResponse else {
                    self.alertMessage = "Invalid server response."
                    self.showAlert = true
                    return
                }
                
                print("--- HTTP STATUS CODE ---")
                print(httpResponse.statusCode) // 打印出具体的状态码，是 422? 400? 500?
                
                if let data = data {
                    print("--- SERVER RESPONSE (RAW) ---")
                    // 尝试将返回的数据转成字符串打印出来
                    print(String(data: data, encoding: .utf8) ?? "Could not print response body")
                }

                // 检查状态码是否成功
                guard (200...299).contains(httpResponse.statusCode) else {
                    // 尝试解析你已有的错误格式
                    if let data = data,
                       let errorDetail = try? JSONDecoder().decode([String: String].self, from: data) {
                        self.alertMessage = "Registration Failed: \(errorDetail["detail"] ?? "unknown error")"
                    } else {
                        self.alertMessage = "Registration failed, please check your input"
                    }
                    self.showAlert = true
                    return
                }
                guard let data = data else {
                    self.alertMessage = "The server did not respond"
                    self.showAlert = true
                    return
                }
                
                do {
                    let decoder = JSONDecoder()

                    // 告诉解码器如何处理日期：服务器用的是标准的 ISO8601 格式
                    decoder.dateDecodingStrategy = .iso8601
                    
                    let decodedResponse = try decoder.decode(RegistrationResponse.self, from: data)
                    
                    self.alertMessage = "User \(decodedResponse.name) registered successfully"
                    self.showAlert = true
                } catch {
                    print("--- JSON DECODING ERROR ---")
                    print(error)
                    self.alertMessage = "Could not parse server response"
                    self.showAlert = true
                }
            }
        }.resume()
    }
}
