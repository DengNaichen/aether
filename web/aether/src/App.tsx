import React from "react";
import { Routes, Route, Link, Navigate } from "react-router-dom";

import RegistrationForm from "./components/RegistrationForm";
import "./App.css";
import TestComponent from "./components/TestComponent";

function LoginPagePlaceholder() {
  return (
    <div>
      <h2>Login</h2>
      <p>Login form will go here .</p>
      <p>
        Don't have an account? {}
        <Link to="/register">Create one now!</Link>
      </p>
    </div>
  );
}

function App() {
  return (
    <div className="App">
      <TestComponent />
      <nav style={{ padding: "1rem", backgroundColor: "#222" }}>
        <Link to="/login" style={{ marginRight: "1rem" }}>
          Login
        </Link>
        <Link to="/register">Register</Link>
      </nav>

      <main className="App-header">
        <Routes>
          <Route path="/register" element={<RegistrationForm />} />
          <Route path="/login" element={<LoginPagePlaceholder />} />
          <Route path="/" element={<Navigate to="/login" />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
