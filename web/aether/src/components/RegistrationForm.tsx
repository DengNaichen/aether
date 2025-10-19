import React, { useState } from "react";
import type {
  RegisterRequest,
  RegisterResponse,
  RawRegisterResponse,
  ErrorResponse,
} from "../types/api";
import {
  tokenManager
} from "../tokenManager";

// import {registerUser} from "../api/auth";
// import {mapRegisterResponse} from "../utils/mapper";
// }

const API_BASE_URL = "https://localhost:8000";

const RegistrationForm: React.FC = () => {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    const registrationData: RegisterRequest = {
      name,
      email,
      password,
    };

    try {
      const response = await fetch(`${API_BASE_URL}/user/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(registrationData),
      });

      const responseData = await response.json();

      if (!response.ok) {
        const errorResponse = responseData as ErrorResponse;
        throw new Error(errorResponse.detail || "Registration failed");
      }

      const rawRegister = responseData as RawRegisterResponse;
      const cleanResponse: RegisterResponse = {
        id: rawRegister.id,
        name: rawRegister.name,
        email: rawRegister.email,
        createdAt: rawRegister.created_at,
      };

      setSuccess(
        `Welcome, ${cleanResponse.name}$! Your account has been created`
      );
      console.log("Registration successful: ", cleanResponse);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center min-h-screen bg-gray-100">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-md p-8 space-y-6 bg-white rounded-lg shadow-md"
      >
        <h2 className="text-2xl font-bold text-center text-gray-900">
          {" "}
          Create Account{" "}
        </h2>
        <div>
          <label
            htmlFor="name"
            className="block text-sm font-medium, text-gray-700"
          >
            Name:
          </label>
          <input
            id="name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus: ring-indigo-500 focus: border-indigo-500"
          />
        </div>
        <div>
          <label
            htmlFor="email"
            className="block text-sm font-medium, text-gray-700"
          >
            Email:
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus: ring-indigo-500 focus: border-indigo-500"
          />
        </div>
        <div>
          <label
            htmlFor="password"
            className="block text-sm font-medium, text-gray-700"
          >
            Email:
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus: ring-indigo-500 focus: border-indigo-500"
          />
        </div>
        {error && <p style={{ color: "red" }}>{error}</p>}
        {success && <p style={{ color: "green" }}>{success}</p>}
        <button type="submit" disabled={loading}>
          {loading ? "Creating Account ..." : "Register"}
        </button>
      </form>
    </div>
  );
};

export default RegistrationForm;
