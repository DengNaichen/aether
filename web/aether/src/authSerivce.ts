import { tokenManager } from "./tokenManager";
import { User } from "./types/api";
import { create } from "zustand";

interface AuthState {
  isAuthenticated: boolean;
  currentUser: User | null;
}

interface AuthActions {
  getAccessToken: () => string | undefined;
  checkAuthenticationStatus: () => void;
  logout: () => void;
  toggleAuthForDemo: () => void;
}

const useAuthStore = create<AuthState & AuthActions>((set, get) => ({
  // --- STATE ---
  isAuthenticated: !!tokenManager.getRefreshToken(),
  currentUser: null, // Initially, we have no user object

  // --- ACTIONS & GETTERS
  /**
   * Getter to retrieve the current access token.
   * @returns accessToken string.
   */
  getAccessToken: () => {
    return tokenManager.getAccessToken();
  },

  checkAuthenticationStatus: () => {
    set({ isAuthenticated: !!tokenManager.getRefreshToken() });
  },

  logout: () => {
    tokenManager.clearTokens();
    set({ isAuthenticated: false, currentUser: null });
    console.log("User logged out");
  },

  toggleAuthForDemo: () => {
    const currentState = get().isAuthenticated
    set({isAuthenticated : !currentState})
    console.log(`Authentication status toggled to ${!currentState}`)
  },
}));

export default useAuthStore;
