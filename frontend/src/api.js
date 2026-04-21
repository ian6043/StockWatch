import { mockWatchlistItems, mockStockData } from "./mockData";

const USE_MOCK = true;

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const API_KEY = import.meta.env.VITE_API_KEY ?? "";
const USER_ID = import.meta.env.VITE_USER_ID ?? "default";

// In-memory mock state so mutations work during the session
let mockItems = mockWatchlistItems.map((item) => ({
  ...item,
  rules: [...item.rules],
}));
let nextItemId = mockItems.length + 1;
let nextRuleId = 10;

function apiFetch(path, options = {}) {
  return fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-Api-Key": API_KEY,
      ...options.headers,
    },
  }).then((res) => {
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    return res.json();
  });
}

// GET /users/{user_id}/watchlist
export async function getWatchlist() {
  if (USE_MOCK) return mockItems.map((i) => ({ ...i, rules: [...i.rules] }));
  return apiFetch(`/users/${USER_ID}/watchlist`);
}

// POST /users/{user_id}/watchlist  body: { symbol }
export async function addStock(symbol) {
  if (USE_MOCK) {
    const item = { id: nextItemId++, symbol: symbol.toUpperCase(), rules: [] };
    mockItems = [...mockItems, item];
    return { ...item };
  }
  return apiFetch(`/users/${USER_ID}/watchlist`, {
    method: "POST",
    body: JSON.stringify({ symbol }),
  });
}

// DELETE /users/{user_id}/watchlist/{symbol}
export async function removeStock(symbol) {
  if (USE_MOCK) {
    mockItems = mockItems.filter((s) => s.symbol !== symbol);
    return { message: "Stock removed from watchlist" };
  }
  return apiFetch(`/users/${USER_ID}/watchlist/${symbol}`, { method: "DELETE" });
}

// GET /stock/{symbol}
export async function getStockData(symbol) {
  if (USE_MOCK) return mockStockData[symbol] ?? null;
  return apiFetch(`/stock/${symbol}`);
}

// POST /users/{user_id}/watchlist/{symbol}/rules
export async function addRule(symbol, rule) {
  if (USE_MOCK) {
    const newRule = { id: nextRuleId++, ...rule, last_triggered_at: null };
    const item = mockItems.find((i) => i.symbol === symbol);
    if (item) item.rules = [...item.rules, newRule];
    return { ...newRule };
  }
  return apiFetch(`/users/${USER_ID}/watchlist/${symbol}/rules`, {
    method: "POST",
    body: JSON.stringify(rule),
  });
}

// DELETE /users/{user_id}/watchlist/{symbol}/rules/{rule_id}
export async function deleteRule(symbol, ruleId) {
  if (USE_MOCK) {
    const item = mockItems.find((i) => i.symbol === symbol);
    if (item) item.rules = item.rules.filter((r) => r.id !== ruleId);
    return { message: "Rule deleted" };
  }
  return apiFetch(`/users/${USER_ID}/watchlist/${symbol}/rules/${ruleId}`, {
    method: "DELETE",
  });
}
