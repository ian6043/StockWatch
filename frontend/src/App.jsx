import Watchlist from "./components/Watchlist";
import "./App.css";

export default function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>StockWatch</h1>
      </header>
      <main className="app-main">
        <Watchlist />
      </main>
    </div>
  );
}
