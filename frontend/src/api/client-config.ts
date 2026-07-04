import { tokenStorage } from "@/auth/token-storage";

const BASE_URL = "/api";

export interface CustomFetchOptions extends RequestInit {
  baseUrl?: string;
}

export interface CustomFetchError extends Error {
  status: number;
  payload: unknown;
}

function buildResponse<T>(payload: unknown, response: Response): T {
  return {
    data: payload,
    status: response.status,
    headers: response.headers,
  } as T;
}

async function doFetch(
  url: string,
  options: CustomFetchOptions,
): Promise<{ payload: unknown; response: Response }> {
  const baseUrl = options.baseUrl ?? BASE_URL;
  const fullUrl = url.startsWith("http") ? url : `${baseUrl}${url}`;

  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }
  const accessToken = tokenStorage.getAccessToken();
  if (accessToken && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  const response = await fetch(fullUrl, { ...options, headers });
  const payload = await parseResponse(response);
  return { payload, response };
}

async function parseResponse(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

let isRefreshing = false;
let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  if (isRefreshing && refreshPromise) return refreshPromise;
  const refreshToken = tokenStorage.getRefreshToken();
  if (!refreshToken) return null;

  isRefreshing = true;
  refreshPromise = (async () => {
    try {
      const { payload, response } = await doFetch("/auth/refresh", {
        method: "POST",
        body: JSON.stringify({ refreshToken }),
      });
      if (!response.ok) throw new Error("refresh failed");
      const data = payload as { accessToken: string; refreshToken: string };
      tokenStorage.setTokens(data.accessToken, data.refreshToken);
      return data.accessToken;
    } catch {
      tokenStorage.clear();
      return null;
    } finally {
      isRefreshing = false;
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

export async function customFetch<T>(
  url: string,
  options: CustomFetchOptions = {},
): Promise<T> {
  try {
    const { payload, response } = await doFetch(url, options);
    if (!response.ok) {
      const message =
        typeof payload === "object" &&
        payload !== null &&
        "message" in payload &&
        typeof (payload as { message: unknown }).message === "string"
          ? (payload as { message: string }).message
          : `Request failed with status ${response.status}`;
      const error = new Error(message) as CustomFetchError;
      error.status = response.status;
      error.payload = payload;
      throw error;
    }
    return buildResponse<T>(payload, response);
  } catch (err) {
    const error = err as CustomFetchError;
    if (error.status === 401 && !url.includes("/auth/")) {
      const newToken = await refreshAccessToken();
      if (newToken) {
        const headers = new Headers(options.headers);
        headers.set("Authorization", `Bearer ${newToken}`);
        const { payload, response } = await doFetch(url, {
          ...options,
          headers,
        });
        if (!response.ok) {
          const fresh = new Error(
            typeof payload === "object" &&
              payload !== null &&
              "message" in payload
              ? String((payload as { message: unknown }).message)
              : `Request failed with status ${response.status}`,
          ) as CustomFetchError;
          fresh.status = response.status;
          fresh.payload = payload;
          throw fresh;
        }
        return buildResponse<T>(payload, response);
      }
    }
    throw error;
  }
}
