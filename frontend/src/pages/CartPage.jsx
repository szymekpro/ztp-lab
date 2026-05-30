import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { apiDelete, apiGet, apiPost } from "../api/client";
import Navbar from "../components/Navbar";
import useCurrentOperator from "../hooks/useCurrentOperator";

function CartPage() {
  const { authLoading, authError } = useCurrentOperator();
  const navigate = useNavigate();

  const [cart, setCart] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function loadCart() {
    try {
      const data = await apiGet("/api/v1/cart");
      setCart(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!authLoading && !authError) {
      loadCart();
    }
  }, [authLoading, authError]);

  async function handleRemoveItem(itemId) {
    setMessage("");
    setError("");

    try {
      await apiDelete("/api/v1/cart/items/" + itemId);
      setMessage("Produkt zostało usunięte z koszyka.");
      await loadCart();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleUpdateQuantity(itemId, newQuantity) {
    setMessage("");
    setError("");

    if (newQuantity <= 0) {
      return handleRemoveItem(itemId);
    }

    try {
      const apiPatch = (await import("../api/client")).apiPatch;
      await apiPatch("/api/v1/cart/items/" + itemId, {
        quantity: newQuantity,
      });
      await loadCart();
    } catch (err) {
      setError(err.message);
    }
  }
  
  async function handleCheckout() {
    setMessage("");
    setError("");

    try {
      await apiPost("/api/v1/cart/checkout");
      setMessage("Zamówienie zostało złożone.");
      navigate("/orders");
    } catch (err) {
      setError(err.message);
    }
  }

  if (authLoading) {
    return (
      <main className="page">
        <section className="card">
          <p>Sprawdzanie sesji...</p>
        </section>
      </main>
    );
  }

  if (authError) {
    return null;
  }

  return (
    <>
      <Navbar />

      <main className="page">
        <section className="card wide-card">
          <h1>Koszyk</h1>

          {loading && <p>Ladowanie koszyka...</p>}

          {error && <p className="error">{error}</p>}

          {message && <p className="success">{message}</p>}

          {!loading && !error && cart && (
            <>
              <div className="details" style={{ marginBottom: '32px' }}>
                <p>
                  <strong>Liczba produktow:</strong> {cart.items_count}
                </p>

                <p>
                  <strong>Suma:</strong> {cart.total_price} zł
                </p>
                
                <button 
                  onClick={handleCheckout} 
                  disabled={cart.items.length === 0}
                  style={{ marginTop: '12px', padding: '10px 20px', fontSize: '16px', cursor: 'pointer' }}
                >
                  Złóż zamówienie
                </button>
              </div>

              {cart.items.length === 0 ? (
                <p>Koszyk jest pusty.</p>
              ) : (
                <div className="product-list">
                  {cart.items.map((item) => (
                    <article key={item.id} className="product-item">
                      <div>
                        <strong>
                          {item.product.name}
                        </strong>

                        <p>Cena jednostkowa: {item.product.price} zł</p>
                        <p>Ilość w koszyku: {item.quantity}</p>
                        <p><strong>Cena pozycji: {item.product.price * item.quantity} zł</strong></p>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '5px', marginTop: '10px' }}>
                        <button style={{ margin: 0, alignSelf: 'center' }} onClick={() => handleUpdateQuantity(item.id, item.quantity - 1)}>-</button>
                        <button style={{ margin: 0, alignSelf: 'center' }} onClick={() => handleUpdateQuantity(item.id, item.quantity + 1)}>+</button>
                        <button style={{ margin: 0, alignSelf: 'center' }} onClick={() => handleRemoveItem(item.id)}>
                          Usuń z koszyka
                        </button>
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </>
          )}
        </section>
      </main>
    </>
  );
}

export default CartPage;

