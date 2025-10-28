enum RequestBody {
    case json(Encodable)
    case formUrlEncoded([String: String])
}

enum HTTPMethod: String {
    case GET, POST, PUT, DELETE
}

protocol Endpoint {
    var path: String { get }
    var method: HTTPMethod { get }
    var body: RequestBody? { get }
    
    var requiredAuth: Bool { get }
}

struct RegisterEndpoint: Endpoint {
    let registrationRequest: RegistrationRequest
    
    var path: String { "/users/register" }
    var method: HTTPMethod { .POST }
    var body: RequestBody? { .json(registrationRequest) }
    var requiredAuth: Bool { false }
}

struct LoginEndpoint: Endpoint {
    let loginData: [String: String]
    
    var path: String { "/users/login" }
    var method: HTTPMethod { .POST }
    var body: RequestBody? { .formUrlEncoded(loginData) }
    
    var requiredAuth: Bool { false }
}

struct AppleSignInEndpoint: Endpoint {
    let appleLoginRequest: AppleSignInRequest
    
    var path: String { "/auth/apple" }
    var method: HTTPMethod { .POST }
    var body: RequestBody? { .json(appleLoginRequest) }
    var requiredAuth: Bool { false }
}

struct GoogleSignInEndpoint: Endpoint {
    let googleLoginRequest: GoogleSignInRequest
    
    var path: String { "/auth/google" }
    var method: HTTPMethod { .POST }
    var body: RequestBody? { .json(googleLoginRequest) }
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

struct GetAllCoursesEndpoint: Endpoint {
    var path: String { "/courses/" }  // Added trailing slash to match FastAPI route
    var method: HTTPMethod { .GET }
    var body: RequestBody? { nil }
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

    var path: String { "/courses/\(courseId)/enrollments" }
    var method: HTTPMethod { .POST }
    var body: RequestBody? {
        .json(EnrollmentRequest(courseId: courseId))
    }

    var requiredAuth: Bool { true }
}

struct RefreshTokenEndpoint: Endpoint {
    let refreshToken: String

    var path: String { "/users/refresh" }
    var method: HTTPMethod { .POST }
    var body: RequestBody? {
        .json(RefreshTokenRequest(refreshToken: refreshToken))
    }
    var requiredAuth: Bool { false }
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
