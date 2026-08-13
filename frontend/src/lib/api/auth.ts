import type { User } from "@/types";
import { clearToken, http, setToken } from "./client";
import { type BackendUser, toUser } from "./adapters";

export interface Credentials {
  email: string;
  password: string;
}

interface BackendLoginResponse {
  access_token: string;
  token_type?: string;
  user?: BackendUser;
}

/** POST /v1/auth/login */
export async function login(payload: Credentials) {
  const data = (await http.post<BackendLoginResponse>("/auth/login", payload)).data;
  setToken(data.access_token);
  return data;
}

/** GET /v1/auth/me */
export async function getCurrentUser(_token: string): Promise<User> {
  return toUser((await http.get<BackendUser>("/auth/me")).data);
}

export function logout() {
  clearToken();
}
