import type { User } from "@/types";
import { http } from "./client";
import { type BackendUser, toUser } from "./adapters";
import type { Role } from "@/types";

/**
 * GET /v1/users — present only on backends that expose user management.
 * Role/permission mutations are intentionally NOT implemented here: the
 * backend owns role assignment and no update endpoint is assumed.
 */
export async function list(): Promise<User[]> {
  return (await http.get<BackendUser[]>("/users")).data.map(toUser);
}

export interface CreateUserPayload {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  role: Exclude<Role, "OWNER">;
  warehouse_ids: string[];
}

/** POST /v1/users */
export async function create(payload: CreateUserPayload): Promise<User> {
  return toUser((await http.post<BackendUser>("/users", payload)).data);
}
