import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { apiGet, apiRequest } from "../api/client";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
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
  const [cancelLoading, setCancelLoading] = useState(false);

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

  async function handleCancelOrder() {
    const confirmed = window.confirm(
      "Czy na pewno chcesz anulować to zamówienie?"
    );

    if (!confirmed) {
      return;
    }

    setActionError("");
    setSuccessMessage("");
    setCancelLoading(true);

    try {
      await apiRequest(`/api/v1/orders/${orderId}/cancel`, {
        method: "POST",
      });

      setSuccessMessage("Zamówienie zostało anulowane.");
      await loadOrderDetails();
    } catch (err) {
      setActionError(err.message);
    } finally {
      setCancelLoading(false);
    }
  }

  if (authLoading) {
    return (
      <main className="page">
        <section className="card">
          <LoadingState message="Sprawdzanie sesji..." />
        </section>
      </main>
    );
  }

  if (authError) {
    return null;
  }

  const isActionLoading = completeLoading || cancelLoading;

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
            <LoadingState message="Ładowanie szczegółów zamówienia..." />
          )}

          {loadError && <ErrorState message={loadError} />}

          {actionError && <ErrorState message={actionError} />}

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
                    disabled={isActionLoading}
                    onClick={handleCompleteOrder}
                  >
                    {completeLoading
                      ? "Finalizowanie zamówienia..."
                      : "Sfinalizuj zamówienie"}
                  </button>

                  <button
                    disabled={isActionLoading}
                    onClick={handleCancelOrder}
                  >
                    {cancelLoading
                      ? "Anulowanie..."
                      : "Anuluj zamówienie"}
                  </button>
                </div>
              ) : (
                <div className="info-box">
                  <p>
                    To zamówienie ma status{" "}
                    <strong>{order.status}</strong> i nie można wykonać na nim
                    kolejnej operacji zmiany statusu.
                  </p>
                </div>
              )}

              {order.items.length === 0 ? (
                <EmptyState title="Brak produktów w zamówieniu." />
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
