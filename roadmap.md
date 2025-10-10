# 🗺️ Roadmap
## User Authentication
- [ ] Backend API
    - [x] Database design
    - [ ] API endpoint:
        - [x] `POST/auth/register`
        - [x] `POST/auth/login`
        - [ ] `POST/auth/logout`
        - [x] `POST/user/me`
    - [x] Token: Implement the JWT assignment, velidation and refresh
- [ ] iOS Client
    - [x] UI/UX
    - [x] Network Layer: implement the api service
    - [ ] Session Management
- [ ] OAuth 2.0 Intergration:
    - [ ] Backend:
        - [ ] Configure projects in Google Cloud Platform and Apple Developer to obtain client credentials.
        - [ ] Implement API endpoints to handle OAuth callbacks from Google and Apple.
        - [ ] Develop logic to link OAuth identities to new or existing user accounts.
    - [ ] iOS:
        - [ ] Integrate the Google Sign-In SDK and Sign in with Apple SDK.
        - [ ] Add "Sign in with Google" and "Sign in with Apple" buttons to the login screen and implement their functionality.

## Knowledge Graph Construction
- [x] Data Modeling:
    - [x] Define node types: `Concept`, `Problem`, `User`.
    - [x] Define edge/relationship types: `is_prerequisite_for`, `is_related_to`, `tests`, etc.
- [ ] Content Population - example: G11 Chemistry:
    - [ ] Curate and structure concepts for key units (e.g., Stoichiometry, Atomic Structure, Chemical Bonds).
    - [ ] Input the concepts and their relationships into the database.

## Bayesian Knowledge Tracing (BKT) Algorithm Implementation
- [x] Research: Finalize the four core BKT parameters: $P(L_0)$ (prior knowledge), $P(T)$ (transition/learning rate), $P(G)$ (guess), and $P(S)$ (slip).
- [ ] Backend Development:
    - [ ] Database Schema: Create a `student_knowledge_states` table to store `user_id`, `concept_id`, and `probability_known`.
    - [ ] BKT Update Service: Create a service that processes a student's answer (e.g., problem ID, correctness) and updates the student's knowledge probability for the associated concepts using the BKT formulas.
    - [ ] **API Endpoint:** Create a `POST /submissions` endpoint to receive problem-solving results from the client and trigger the BKT update process.

## ~~Learning Path Visualization~~

## Improve Test Coverage
- [ ] Framework Setup: Configure `pytest` for the backend and `XCTest` for the iOS project.
- [ ] Backend Testing:
    - [ ] Unit Tests: Write tests for critical business logic, including authentication services, BKT calculations, and recommendation algorithms.
    - [ ] Integration Tests: Write tests for API endpoints to ensure correct interaction with the database and other services.
- [ ] iOS Testing:
    - [ ] Unit Tests: Write tests for ViewModels and data models.
    - [ ] UI Tests: Automate tests for key user flows like login, problem submission, and navigation.
- [ ] CI/CD Integration: Integrate automated testing into a CI/CD pipeline (e.g., GitHub Actions) to run on every commit.