import Watchlist from "./components/Watchlist";
import Settings from "./components/Settings";
import "./App.css";

export default function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>StockWatch</h1>
        <p className="welcome">Welcome, {import.meta.env.VITE_USER_ID ?? "there"}</p>
      </header>
      <main className="app-main">
        <Watchlist />
        <Settings />
      </main>
    </div>
  );
}
