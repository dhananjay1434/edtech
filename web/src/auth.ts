import Keycloak from "keycloak-js";

const keycloak = new Keycloak({
  url: import.meta.env.VITE_KEYCLOAK_URL ?? "http://localhost:8080",
  realm: import.meta.env.VITE_KEYCLOAK_REALM ?? "cde",
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID ?? "cde-web",
});

export async function initAuth(): Promise<boolean> {
  return keycloak.init({ onLoad: "login-required", pkceMethod: "S256",
                          checkLoginIframe: false });
}

export const getToken = () => keycloak.token;
export const hasRole = (r: string) => keycloak.hasRealmRole(r);
export const logout = () => keycloak.logout();

export async function authFetch(url: string, options: RequestInit = {}) {
  await keycloak.updateToken(30);
  return fetch(url, { ...options, headers: {
    ...(options.headers ?? {}), Authorization: `Bearer ${keycloak.token}` } });
}

export default keycloak;
