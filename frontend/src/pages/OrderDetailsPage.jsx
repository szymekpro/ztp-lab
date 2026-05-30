import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { apiGet, apiRequest } from "../api/client";
import Navbar from "../components/Navbar";
import StatusBadge from "../components/StatusBadge";
import useCurrentOperator from "../hooks/useCurrentOperator";

function OrderDetailsPage() {
  const { orderId } = useParams();
  const { authLoading, authError } = useCurrentOperator();

  const [order, setOrder] = useState(null);

  const [loadError, setLoadError] = useState("");
  const [actionError, setActionError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const [loading, setLoading] = useState(true);
  const [completeLoading, setCompleteLoading] = useState(false);

  async function loadOrderDetails() {
    setLoadError("");

    try {
      const data = await apiGet(`/api/v1/orders/${orderId}`);
      setOrder(data);
    } catch (err) {
      setLoadError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!authLoading && !authError) {
      loadOrderDetails();
    }
  }, [authLoading, authError, orderId]);

  async function handleCompleteOrder() {
    setActionError("");
    setSuccessMessage("");
    setCompleteLoading(true);

    try {
      await apiRequest(`/api/v1/orders/${orderId}/complete`, {
        method: "POST",
        headers: {
          "Idempotency-Key": crypto.randomUUID(),
        },
      });

      setSuccessMessage("Zamówienie zostało sfinalizowane.");
      await loadOrderDetails();
    } catch (err) {
      setActionError(err.message);
    } finally {
      setCompleteLoading(false);
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
          <Link to="/orders" className="back-link">
            ← Wróć do historii zamówień
          </Link>

          <h1>Szczegóły zamówienia</h1>

          {loading && (
            <div className="state-box">
              <p>Ładowanie szczegółów zamówienia...</p>
            </div>
          )}

          {loadError && (
            <div className="state-box error-box">
              <p>{loadError}</p>
            </div>
          )}

          {actionError && (
            <div className="state-box error-box">
              <p>{actionError}</p>
            </div>
          )}

          {successMessage && (
            <div className="state-box success-box">
              <p>{successMessage}</p>
            </div>
          )}

          {!loading && !loadError && order && (
            <>
              <div className="details">
                <p>
                  <strong>Numer:</strong> {order.order_number}
                </p>

                <p>
                  <strong>Status:</strong>{" "}
                  <StatusBadge status={order.status} />
                </p>

                <p>
                  <strong>Liczba produktów:</strong> {order.items_count}
                </p>

                <p>
                  <strong>Suma zamówienia:</strong> {order.total_price} zł
                </p>
              </div>

              {order.status === "PENDING" ? (
                <div className="actions-bar">
                  <button
                    disabled={completeLoading}
                    onClick={handleCompleteOrder}
                  >
                    {completeLoading
                      ? "Finalizowanie zamówienia..."
                      : "Sfinalizuj zamówienie"}
                  </button>
                </div>
              ) : (
                <div className="info-box">
                  <p>
                    To zamówienie ma status{" "}
                    <strong>{order.status}</strong> i nie może zostać
                    ponownie sfinalizowane.
                  </p>
                </div>
              )}

              {order.items.length === 0 ? (
                <div className="empty-state">
                  <p>Brak produktów w zamówieniu.</p>
                </div>
              ) : (
                <div className="order-product-list">
                  {order.items.map((item) => (
                    <article key={item.id} className="order-product-item">
                      <div>
                        <strong>{item.product_name}</strong>

                        <p>Cena jednostkowa: {item.product_price} zł</p>
                        <p>Ilość: {item.quantity}</p>
                        <p>
                          <strong>
                            Suma pozycji:{" "}
                            {(item.product_price * item.quantity).toFixed(2)} zł
                          </strong>
                        </p>
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

export default OrderDetailsPage;
