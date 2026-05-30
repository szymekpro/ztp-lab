import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { apiGet } from "../api/client";
import Navbar from "../components/Navbar";
import StatusBadge from "../components/StatusBadge";
import useCurrentOperator from "../hooks/useCurrentOperator";

function OrdersPage() {
  const { authLoading, authError } = useCurrentOperator();

  const [orders, setOrders] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function loadOrders() {
    try {
      const data = await apiGet("/api/v1/orders");
      setOrders(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!authLoading && !authError) {
      loadOrders();
    }
  }, [authLoading, authError]);

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
          <h1>Historia zamówień</h1>

          {loading && <p>Ładowanie zamówień...</p>}

          {error && <p className="error">{error}</p>}

          {!loading && !error && orders.length === 0 && (
            <div className="empty-state">
              <p>Brak złożonych zamówień.</p>

              <p>
                Przejdź do koszyka, dodaj produkty i złóż zamówienie.
              </p>
            </div>
          )}

          {!loading && !error && orders.length > 0 && (
            <div className="order-list">
              {orders.map((order) => (
                <article key={order.id} className="order-item">
                  <div>
                    <strong>{order.order_number}</strong>

                    <p>
                      Liczba produktów: {order.items_count}
                    </p>

                    <p>
                      Suma: {order.total_price} zł
                    </p>
                  </div>

                  <div className="order-actions">
                    <StatusBadge status={order.status} />

                    <Link to={`/orders/${order.id}`}>
                      Szczegóły
                    </Link>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </main>
    </>
  );
}

export default OrdersPage;
