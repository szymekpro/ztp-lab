import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";

import { apiPost } from "../api/client";

function RegisterPage() {
  const navigate = useNavigate();

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");

  const [email, setEmail] = useState("");

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      await apiPost("/api/v1/auth/register", {
        first_name: firstName,
        last_name: lastName,
        email: email,
        password: password,
        confirm_password: confirmPassword,
      });

      navigate("/login");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <section className="card">
        <h1>Rejestracja</h1>

        <form onSubmit={handleSubmit} className="form">
          <label>
            Imię
            <input
              type="text"
              value={firstName}
              onChange={(event) => setFirstName(event.target.value)}
            />
          </label>

          <label>
            Nazwisko
            <input
              type="text"
              value={lastName}
              onChange={(event) => setLastName(event.target.value)}
            />
          </label>

          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>

          <label>
            Hasło
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>

          <label>
            Powtórz hasło
            <input
              type="password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
            />
          </label>

          {error && (
            <p className="error">
              {error}
            </p>
          )}

          <button type="submit" disabled={loading}>
            {loading ? "Tworzenie konta..." : "Zarejestruj"}
          </button>
        </form>

        <p className="auth-link">
          Masz już konto? <Link to="/login">Zaloguj się</Link>
        </p>
      </section>
    </main>
  );
}

export default RegisterPage;
