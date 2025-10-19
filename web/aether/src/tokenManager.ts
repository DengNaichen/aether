import Cookies from "js-cookie";

const ACCESS_TOKEN_KEY = "auth_access_token";
const REFRESH_TOKEN_KEY = "auth_refresh_token";

class TokenManager {
  private static _instance: TokenManager;

  // The constructor function is private, make sure cannot create the instance
  // by new TokenManager()
  private constructor() {}

  /**
   * Obtain the singleton token manager.
   * @returns The singleton Token manager instance.
   */
  public static getInstance(): TokenManager {
    if (!TokenManager._instance) {
      TokenManager._instance = new TokenManager();
    }
    return TokenManager._instance;
  }

  /**
   * save the access and refresh token to cookie
   * @param accessToken - the access token gonna be saved
   * @param refreshToken - the refresh token gonna be saved
   */
  public saveToken(accessToken: string, refreshToken: string): void {
    const cookieOptions = {
      expires: 7,
      secure: true, ///// TODO: don't know to do this part
      sameSite: "strict" as const,
    };

    Cookies.set(ACCESS_TOKEN_KEY, accessToken, cookieOptions);
    Cookies.set(REFRESH_TOKEN_KEY, refreshToken, cookieOptions);
    console.log("Tokens saved to Cookies");
  }

  /**
   * Obtain the access token from cookie
   * @returns access token string, if not exist, return undefined
   */
  public getAccessToken(): string | undefined {
    return Cookies.get(ACCESS_TOKEN_KEY);
  }

  /**
   * Obtain the refresh token from cookie
   * @returns refresh token string, if not exist, return undefined
   */
  public getRefreshToken(): string | undefined {
    return Cookies.get(REFRESH_TOKEN_KEY);
  }

  /**
   * clean all the token from cookie
   */
  public clearTokens(): void {
    Cookies.remove(ACCESS_TOKEN_KEY);
    Cookies.remove(REFRESH_TOKEN_KEY);
    console.log("Tokens cleared from Cookies.");
  }
}

export const tokenManager = TokenManager.getInstance();
