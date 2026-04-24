import { useState } from "react";
import { addRule, deleteRule } from "../api";
import "./RulesPanel.css";

const COOLDOWN_OPTIONS = [
  { label: "5 min",   value: 300 },
  { label: "15 min",  value: 900 },
  { label: "30 min",  value: 1800 },
  { label: "1 hour",  value: 3600 },
  { label: "1 day",   value: 86400 },
];

function formatRule(rule) {
  if (rule.rule_type === "percent_change") {
    const direction = rule.condition === "above" ? "rises above" : "drops above";
    return `% change ${direction} ${Math.abs(rule.target_value).toFixed(2)}%`;
  }
  const direction = rule.condition === "above" ? "above" : "below";
  return `price ${direction} $${rule.target_value.toFixed(2)}`;
}

function formatCooldown(seconds) {
  if (seconds < 60) return `${seconds}s cooldown`;
  if (seconds < 3600) return `${seconds / 60}m cooldown`;
  if (seconds < 86400) return `${seconds / 3600}h cooldown`;
  return `${seconds / 86400}d cooldown`;
}

export default function RulesPanel({ symbol, rules, onRulesChange }) {
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    rule_type: "price",
    condition: "above",
    target_value: "",
    cooldown_seconds: 86400,
  });
  const [error, setError] = useState(null);

  function handleFormChange(e) {
    const { name, value } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: value,
      // reset condition to a valid option when switching rule type
      ...(name === "rule_type" ? { condition: "above", target_value: "" } : {}),
    }));
  }

  async function handleAdd(e) {
    e.preventDefault();
    const value = parseFloat(form.target_value);
    if (isNaN(value)) return;
    // For % change drops, negate so backend checks day_percent_change < -X
    const targetValue =
      form.rule_type === "percent_change" && form.condition === "below"
        ? -Math.abs(value)
        : Math.abs(value);
    try {
      const rule = await addRule(symbol, {
        rule_type: form.rule_type,
        condition: form.condition,
        target_value: targetValue,
        cooldown_seconds: parseInt(form.cooldown_seconds),
      });
      onRulesChange([...rules, rule]);
      setForm({ rule_type: "price", condition: "above", target_value: "", cooldown_seconds: 86400 });
      setShowForm(false);
      setError(null);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleDelete(ruleId) {
    try {
      await deleteRule(symbol, ruleId);
      onRulesChange(rules.filter((r) => r.id !== ruleId));
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="rules-panel">
      {rules.length === 0 && !showForm ? (
        <p className="no-rules">No alert rules set.</p>
      ) : (
        <ul className="rule-list">
          {rules.map((rule) => (
            <li key={rule.id} className="rule-row">
              <span className="rule-label">{formatRule(rule)}</span>
              <span className="rule-cooldown">{formatCooldown(rule.cooldown_seconds)}</span>
              <button
                className="delete-rule-btn"
                onClick={() => handleDelete(rule.id)}
                aria-label="Delete rule"
              >
                ✕
              </button>
            </li>
          ))}
        </ul>
      )}

      {showForm ? (
        <form className="rule-form" onSubmit={handleAdd}>
          <select name="rule_type" value={form.rule_type} onChange={handleFormChange}>
            <option value="price">Price</option>
            <option value="percent_change">% Change</option>
          </select>
          <select name="condition" value={form.condition} onChange={handleFormChange}>
            {form.rule_type === "percent_change" ? (
              <>
                <option value="above">Rise</option>
                <option value="below">Drop</option>
              </>
            ) : (
              <>
                <option value="above">Above</option>
                <option value="below">Below</option>
              </>
            )}
          </select>
          <input
            type="number"
            name="target_value"
            placeholder={form.rule_type === "percent_change" ? "%" : "$"}
            value={form.target_value}
            onChange={handleFormChange}
            step="any"
            required
          />
          <select
            name="cooldown_seconds"
            value={form.cooldown_seconds}
            onChange={handleFormChange}
          >
            {COOLDOWN_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
          <button type="submit">Save</button>
          <button type="button" className="cancel-btn" onClick={() => setShowForm(false)}>
            Cancel
          </button>
        </form>
      ) : (
        <button className="add-rule-btn" onClick={() => setShowForm(true)}>
          + Add rule
        </button>
      )}

      {error && <p className="rule-error">{error}</p>}
    </div>
  );
}
