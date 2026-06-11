import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { apiGet } from "../api/client";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import LoadingState from "../components/LoadingState";
import Navbar from "../components/Navbar";
import StatusBadge from "../components/StatusBadge";
import useCurrentOperator from "../hooks/useCurrentOperator";

function DashboardPage() {
  const { operator, authLoading, authError } = useCurrentOperator();

  const [summary, setSummary] = useState(null);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [summaryError, setSummaryError] = useState("");

  useEffect(() => {
    async function loadSummary() {
      try {
        const data = await apiGet("/api/v1/orders/dashboard/summary");
        setSummary(data);
      } catch (err) {
        setSummaryError(err.message);
      } finally {
        setSummaryLoading(false);
      }
    }

    if (!authLoading && !authError) {
      loadSummary();
    }
  }, [authLoading, authError]);

  if (authLoading) {
    return (
      <main className="page">
        <section className="card">
          <LoadingState message="Ładowanie danych użytkownika..." />
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
          <h1>Dashboard</h1>

          <p>
            Zalogowany operator: <strong>{operator.email}</strong>
          </p>

          {summaryLoading && (
            <LoadingState message="Ładowanie podsumowania..." />
          )}

          {summaryError && <ErrorState message={summaryError} />}

          {!summaryLoading && !summaryError && summary && (
            <>
              <div className="summary-grid">
                <div className="summary-card">
                  <span>Wszystkie zamówienia</span>
                  <strong>{summary.total_orders}</strong>
                </div>

                <div className="summary-card">
                  <span>Oczekujące</span>
                  <strong>{summary.pending_orders}</strong>
                </div>

                <div className="summary-card">
                  <span>Zakończone</span>
                  <strong>{summary.completed_orders}</strong>
                </div>

                <div className="summary-card">
                  <span>Anulowane</span>
                  <strong>{summary.cancelled_orders}</strong>
                </div>
              </div>

              <div className="recent-orders">
                <div className="recent-orders-header">
                  <h2>Ostatnie zamówienia</h2>

                  <Link to="/orders" className="recent-orders-link">
                    Zobacz wszystkie
                  </Link>
                </div>

                {summary.recent_orders.length === 0 ? (
                  <EmptyState
                    title="Brak zamówień."
                    description="Złóż pierwsze zamówienie, aby zobaczyć je w dashboardzie."
                  />
                ) : (
                  <div className="order-list">
                    {summary.recent_orders.map((order, index) => (
                      <article
                        key={order.id}
                        className={
                          index === 0 ? "order-item order-item-latest" : "order-item"
                        }
                      >
                        <div>
                          <div className="order-item-title">
                            <strong>{order.order_number}</strong>

                            {index === 0 && (
                              <span className="latest-tag">Najnowsze</span>
                            )}
                          </div>

                          <p>Liczba produktów: {order.items_count}</p>

                          <p>Suma: {order.total_price} zł</p>
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
              </div>
            </>
          )}
        </section>
      </main>
    </>
  );
}

export default DashboardPage;
