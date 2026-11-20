import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;
export const supabase = supabaseUrl && supabaseAnonKey
  ? createClient(supabaseUrl, supabaseAnonKey)
  : null;

export function getGuestId() {
  const key = "eduplay.guest-id";
  let id = localStorage.getItem(key);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(key, id);
  }
  return id;
}

export async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...options.headers };
  if (supabase) {
    const { data } = await supabase.auth.getSession();
    const token = data.session?.access_token;
    if (token) headers.Authorization = `Bearer ${token}`;
  }
  const response = await fetch(`/api${path}`, {
    ...options,
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });
  const responseBody = await response.text();
  let payload = {};
  try {
    payload = responseBody ? JSON.parse(responseBody) : {};
  } catch {
    throw new Error(
      `The server returned a non-JSON response for ${path} (HTTP ${response.status}). Check the backend logs for the error.`,
    );
  }
  if (!response.ok) {
    const message = payload && typeof payload === "object"
      ? payload.error || payload.detail
      : null;
    throw new Error(message || `Request to ${path} failed (${response.status}).`);
  }
  return payload;
}

export function withGuestId(data = {}) {
  return { ...data, player_id: getGuestId() };
}

