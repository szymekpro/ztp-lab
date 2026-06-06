import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";

import { apiPost } from "../api/client";

function LoginPage() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("user@example.com");
  const [password, setPassword] = useState("String123!");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function validateForm() {
    if (!email.trim()) {
      return "Email jest wymagany.";
    }

    const emailRegex = /\S+@\S+\.\S+/;

    if (!emailRegex.test(email)) {
      return "Niepoprawny adres email.";
    }

    if (!password.trim()) {
      return "Hasło jest wymagane.";
    }

    return null;
  }

  async function handleSubmit(event) {
    event.preventDefault();

    setError("");

    const validationError = validateForm();

    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);

    try {
      await apiPost("/api/v1/auth/login", {
        email: email,
        password: password,
      });

      navigate("/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <section className="card">
        <h1>Logowanie</h1>

        <form onSubmit={handleSubmit} className="form">
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

          {error && <p className="error">{error}</p>}

          <button type="submit" disabled={loading}>
            {loading ? "Logowanie..." : "Zaloguj"}
          </button>
        </form>
        <p className="auth-link">
            Nie masz konta? <Link to="/register">Zarejestruj się</Link>
        </p>
      </section>
    </main>
  );
}

export default LoginPage;
