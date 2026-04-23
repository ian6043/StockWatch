import { useState, useEffect } from "react";
import { getUser, updatePhone } from "../api";
import "./Settings.css";

// Accepts E.164 (+12223334444) or common US formats, normalises to E.164
function parsePhone(raw) {
  const digits = raw.replace(/\D/g, "");
  if (digits.length === 10) return `+1${digits}`;
  if (digits.length === 11 && digits.startsWith("1")) return `+${digits}`;
  return null;
}

function validatePhone(raw) {
  if (!raw.trim()) return "Phone number is required.";
  if (!parsePhone(raw)) return "Enter a valid US number (e.g. 555-867-5309).";
  return null;
}

export default function Settings() {
  const [current, setCurrent] = useState(null);
  const [input, setInput] = useState("");
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getUser()
      .then((user) => {
        setCurrent(user.phone_number);
        setInput(user.phone_number ?? "");
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    const validationError = validatePhone(input);
    if (validationError) { setError(validationError); return; }

    const normalised = parsePhone(input);
    setSaving(true);
    setError(null);
    setSuccess(false);

    try {
      const user = await updatePhone(normalised);
      setCurrent(user.phone_number);
      setInput(user.phone_number);
      setSuccess(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  const isDirty = parsePhone(input) !== current;

  if (loading) return null;

  return (
    <section className="settings">
      <h2>Settings</h2>
      <form className="settings-form" onSubmit={handleSubmit} noValidate>
        <label htmlFor="phone">Alert phone number</label>
        <div className="phone-row">
          <input
            id="phone"
            type="tel"
            placeholder="555-867-5309"
            value={input}
            onChange={(e) => { setInput(e.target.value); setError(null); setSuccess(false); }}
          />
          <button type="submit" disabled={saving || !isDirty}>
            {saving ? "Saving..." : "Save"}
          </button>
        </div>
        {error && <p className="settings-error">{error}</p>}
        {success && <p className="settings-success">Phone number updated.</p>}
        <p className="settings-hint">
          US numbers only. SMS alerts will be sent here when your rules trigger.
        </p>
      </form>
    </section>
  );
}
