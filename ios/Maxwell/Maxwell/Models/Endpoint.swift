struct RegisterEndpoint: Endpoint {
    let registrationRequest: RegistrationRequest
    
    var path: String { "/user/register" }
    var method: HTTPMethod { .POST }
    var body: RequestBody? { .json(registrationRequest) }
    var requiredAuth: Bool { false }
}

struct LoginEndpoint: Endpoint {
    let loginData: [String: String]
    
    var path: String { "/user/login" }
    var method: HTTPMethod { .POST }
    var body: RequestBody? { .formUrlEncoded(loginData) }
    
    var requiredAuth: Bool { false }
}

struct LogoutEndpoint: Endpoint {
    var path: String { "/user/logout" }
    var method: HTTPMethod { .POST }
    var body: RequestBody? { nil } // TODO: finish the request body
    var requiredAuth: Bool { true }
}

struct GetUserInfoEndpoint: Endpoint {
    var path: String { "/users/me" }
    var method: HTTPMethod { .GET }
    var body: RequestBody? { nil } // TODO: finish the request body
    var requiredAuth: Bool { true }
}

struct GetCoursesEndpoint: Endpoint {
    var path: String { "/courses" }
    var method: HTTPMethod { .GET }
    var body: RequestBody? { nil } // TODO:
    var requiredAuth: Bool { true }
}

struct getCourseEndpoint: Endpoint {
    var courseId: String
    
    var path: String { "/courses/\(courseId)" }
    var method: HTTPMethod { .GET }
    var body: RequestBody? { nil } // TODO:
    var requiredAuth: Bool { true }
}

struct EnrollCourseEndpoint: Endpoint {
    let courseId: String
    
    var path: String { "/courses/\(courseId))/enrollment" }
    var method: HTTPMethod { .POST }
    var body: RequestBody? {
        .json(EnrollmentRequest(courseId: courseId))
    }
    
    var requiredAuth: Bool { true }
}



struct QuizEndpoint: Endpoint {
//    let courseId: String
    
    let startSessionRequest: SessionStartRequest
    
//    var path: String { "/courses/\(courseId)/quizzes" }
    var path: String{"TODO"}
    var method: HTTPMethod { .POST }
    var body: RequestBody? { .json(startSessionRequest) }
    var requiredAuth: Bool { true }
}

//struct SubmitQuizEndpoint: Endpoint {
//    let courseId: String
//    let quizId: String
//    
//    let submitRequest: QuizSubmissionRequest
//    
//    var path: String { "/courses/\(courseId)/quizzes/\(sessionId)" }
//    var method: HTTPMethod { .POST }
//    var body: RequestBody? { .json(submitRequest) }
//    var requiredAuth: Bool { true }
//}
//
//struct
