import axios, { AxiosError } from "axios";

/** Base URL for the live Whitfield FastAPI service. */
export const API_BASE_URL = (import.meta.env["VITE_API_BASE_URL"] as string | undefined) ?? "";
export const LIVE_API = API_BASE_URL.length > 0;

export const TOKEN_KEY = "whitfield.token";

export function getToken() {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}
export function setToken(token: string) {
  window.localStorage.setItem(TOKEN_KEY, token);
}
export function clearToken() {
  window.localStorage.removeItem(TOKEN_KEY);
}

export const http = axios.create({
  baseURL: `${API_BASE_URL}/v1`,
  headers: { "Content-Type": "application/json" },
});

http.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

/** Maps backend/demo failures to a single user-facing message shape. */
export interface NormalizedError {
  status: number;
  message: string;
  fieldErrors?: Record<string, string>;
}

export function normalizeError(error: unknown): NormalizedError {
  if (error && typeof error === "object" && "status" in error && "message" in error) {
    const e = error as { status: number; message: string };
    if (typeof e.status === "number") return { status: e.status, message: e.message };
  }
  const axiosError = error as AxiosError<{ detail?: string | { loc?: (string | number)[]; msg?: string }[] }>;
  if (axiosError?.isAxiosError) {
    const status = axiosError.response?.status ?? 0;
    if (status === 0) return { status: 0, message: "Unable to connect to Whitfield WMS. Try again." };
    const url = axiosError.config?.url ?? "";
    if (url.includes("/auth/login")) {
      if (status === 401) return { status, message: "Invalid email or password." };
      if (status === 403) return { status, message: "This account is not allowed to sign in." };
      if (status === 500) {
        return { status, message: "We couldn't sign you in because the server encountered an error." };
      }
    }
    if (url.includes("/receipts/") && url.includes("/items")) {
      const detail = axiosError.response?.data?.detail;
      const detailText = typeof detail === "string" ? detail : "";
      if (status === 404 && detailText.includes("Product with UPC")) {
        return {
          status,
          message: "Product not found for this UPC. Check the barcode or ask a manager to add the product first.",
        };
      }
      if (status === 400 && detailText.includes("does not belong to the receipt")) {
        return { status, message: "This product belongs to a different seller and cannot be added to this receipt." };
      }
      if (status === 409 && detailText.includes("Cannot edit receipt")) {
        return { status, message: "This receipt has already been completed and can no longer be modified." };
      }
      if (status === 403 && detailText.includes("warehouse")) {
        return { status, message: "You don't have access to this warehouse." };
      }
    }
    if (url.includes("/voice/interpret")) {
      const detail = axiosError.response?.data?.detail;
      const detailText = typeof detail === "string" ? detail : "";
      if (status === 400 && detailText.includes("does not belong to the receipt")) {
        return { status, message: "This product belongs to a different seller and cannot be received on this receipt." };
      }
      if (status === 400 || status === 422) {
        return { status, message: detailText || "I couldn't process that recording. Please try again or enter the quantities manually." };
      }
      if (status === 503) {
        return { status, message: detailText || "Voice services are temporarily unavailable. Please enter the quantities manually." };
      }
    }
    if (status === 403) return { status, message: "You don't have permission to perform this action." };
    const detail = axiosError.response?.data?.detail;
    if (Array.isArray(detail)) {
      const fieldErrors = Object.fromEntries(
        detail
          .filter((entry) => entry?.msg)
          .map((entry) => [String(entry.loc?.at(-1) ?? "form"), entry.msg!]),
      );
      return {
        status,
        message: detail[0]?.msg ?? "Please review the highlighted fields.",
        fieldErrors,
      };
    }
    const message = typeof detail === "string" ? detail : "Something went wrong. Please try again.";
    return { status, message };
  }
  return { status: 500, message: (error as Error)?.message ?? "Unexpected error." };
}

export function errorMessage(error: unknown) {
  return normalizeError(error).message;
}
