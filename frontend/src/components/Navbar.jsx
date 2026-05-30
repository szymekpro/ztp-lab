import { Link, useNavigate } from "react-router-dom";

import { apiPost } from "../api/client";

function Navbar() {
  const navigate = useNavigate();

  async function handleLogout() {
    try {
      await apiPost("/api/v1/auth/logout", {});
    } catch (err) {
      console.error(err);
    } finally {
      navigate("/login");
    }
  }

  return (
    <nav className="navbar">
      <div className="navbar-links">
        <Link to="/dashboard">Dashboard</Link>
        <Link to="/products">Produkty</Link>
        <Link to="/cart">Koszyk</Link>
        <Link to="/orders">Zamówienia</Link>
      </div>

      <button onClick={handleLogout}>
        Wyloguj
      </button>
    </nav>
  );
}

export default Navbar;
