import { useState, useEffect } from "react";
import { getWatchlist, addStock, removeStock, getStockData } from "../api";
import RulesPanel from "./RulesPanel";
import "./Watchlist.css";

export default function Watchlist() {
  const [stocks, setStocks] = useState([]);
  const [stockData, setStockData] = useState({});
  const [expanded, setExpanded] = useState(null);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getWatchlist()
      .then((items) => {
        setStocks(items);
        return Promise.all(
          items.map((item) =>
            getStockData(item.symbol).then((data) => ({ symbol: item.symbol, data }))
          )
        );
      })
      .then((results) => {
        const map = {};
        results.forEach(({ symbol, data }) => { map[symbol] = data; });
        setStockData(map);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  async function handleAdd(e) {
    e.preventDefault();
    const symbol = input.trim().toUpperCase();
    if (!symbol || stocks.find((s) => s.symbol === symbol)) return;
    try {
      const item = await addStock(symbol);
      setStocks((prev) => [...prev, item]);
      const data = await getStockData(symbol);
      setStockData((prev) => ({ ...prev, [symbol]: data }));
      setInput("");
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleRemove(symbol) {
    try {
      await removeStock(symbol);
      setStocks((prev) => prev.filter((s) => s.symbol !== symbol));
      setStockData((prev) => { const next = { ...prev }; delete next[symbol]; return next; });
      if (expanded === symbol) setExpanded(null);
    } catch (err) {
      setError(err.message);
    }
  }

  function toggleExpand(symbol) {
    setExpanded((prev) => (prev === symbol ? null : symbol));
  }

  function handleRulesChange(symbol, newRules) {
    setStocks((prev) =>
      prev.map((s) => (s.symbol === symbol ? { ...s, rules: newRules } : s))
    );
  }

  if (loading) return <p className="status">Loading watchlist...</p>;
  if (error) return <p className="status error">{error}</p>;

  return (
    <section className="watchlist">
      <div className="watchlist-header">
        <h2>Watchlist</h2>
        <form className="add-form" onSubmit={handleAdd}>
          <input
            type="text"
            placeholder="Add symbol..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          <button type="submit">Add</button>
        </form>
      </div>

      {stocks.length === 0 ? (
        <p className="empty">No stocks in your watchlist.</p>
      ) : (
        <ul className="stock-list">
          {stocks.map((stock) => {
            const data = stockData[stock.symbol];
            const isExpanded = expanded === stock.symbol;
            return (
              <li key={stock.symbol} className={`stock-item ${isExpanded ? "expanded" : ""}`}>
                <div
                  className="stock-row"
                  onClick={() => toggleExpand(stock.symbol)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => e.key === "Enter" && toggleExpand(stock.symbol)}
                >
                  <span className={`chevron ${isExpanded ? "open" : ""}`}>›</span>
                  <div className="stock-info">
                    <span className="stock-symbol">{stock.symbol}</span>
                    {data?.name && <span className="stock-name">{data.name}</span>}
                  </div>
                  <div className="stock-price">
                    {data?.price != null ? (
                      <>
                        <span className="price">${data.price.toFixed(2)}</span>
                        <span className={`change ${data.change >= 0 ? "positive" : "negative"}`}>
                          {data.change >= 0 ? "+" : ""}
                          {data.change.toFixed(2)} ({data.changePct.toFixed(2)}%)
                        </span>
                      </>
                    ) : (
                      <span className="no-data">—</span>
                    )}
                  </div>
                  <span className="rule-count">
                    {stock.rules.length > 0 && `${stock.rules.length} rule${stock.rules.length > 1 ? "s" : ""}`}
                  </span>
                  <button
                    className="remove-btn"
                    onClick={(e) => { e.stopPropagation(); handleRemove(stock.symbol); }}
                    aria-label={`Remove ${stock.symbol}`}
                  >
                    ✕
                  </button>
                </div>
                {isExpanded && (
                  <RulesPanel
                    symbol={stock.symbol}
                    rules={stock.rules}
                    onRulesChange={(newRules) => handleRulesChange(stock.symbol, newRules)}
                  />
                )}
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
