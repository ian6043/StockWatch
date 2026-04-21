// Mirrors WatchlistItemResponse from the backend
export const mockWatchlistItems = [
  {
    id: 1, symbol: "AAPL", rules: [
      { id: 1, rule_type: "price", condition: "above", target_value: 200, cooldown_seconds: 300, last_triggered_at: null },
      { id: 2, rule_type: "percent_change", condition: "below", target_value: -3, cooldown_seconds: 600, last_triggered_at: null },
    ],
  },
  { id: 2, symbol: "MSFT", rules: [] },
  { id: 3, symbol: "NVDA", rules: [
      { id: 3, rule_type: "price", condition: "below", target_value: 800, cooldown_seconds: 300, last_triggered_at: null },
    ],
  },
  { id: 4, symbol: "GOOGL", rules: [] },
  { id: 5, symbol: "TSLA", rules: [] },
];

// Mirrors the stock service response shape
export const mockStockData = {
  AAPL:  { symbol: "AAPL",  name: "Apple Inc.",      price: 189.42, change: 1.23,  changePct: 0.65  },
  MSFT:  { symbol: "MSFT",  name: "Microsoft Corp.", price: 415.10, change: -2.85, changePct: -0.68 },
  NVDA:  { symbol: "NVDA",  name: "NVIDIA Corp.",    price: 875.35, change: 22.10, changePct: 2.59  },
  GOOGL: { symbol: "GOOGL", name: "Alphabet Inc.",   price: 174.90, change: 0.55,  changePct: 0.32  },
  TSLA:  { symbol: "TSLA",  name: "Tesla Inc.",      price: 245.67, change: -8.43, changePct: -3.32 },
};
