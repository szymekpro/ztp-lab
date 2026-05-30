import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { apiGet } from "../api/client";
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
          <p>Ładowanie danych użytkownika...</p>
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

          {summaryLoading && <p>Ładowanie podsumowania...</p>}

          {summaryError && <p className="error">{summaryError}</p>}

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

              <div className="last-assignment">
                <h2>Ostatnie zamówienie</h2>

                {summary.last_order ? (
                  <>
                    <p>
                      <strong>Numer:</strong>{" "}
                      {summary.last_order.order_number}
                    </p>

                    <p>
                      <strong>Status:</strong>{" "}
                      <StatusBadge status={summary.last_order.status} />
                    </p>

                    <p>
                      <strong>Liczba produktów:</strong>{" "}
                      {summary.last_order.items_count}
                    </p>

                    <p>
                      <strong>Suma:</strong>{" "}
                      {summary.last_order.total_price} zł
                    </p>

                    <Link to={`/orders/${summary.last_order.id}`}>
                      Zobacz szczegóły
                    </Link>
                  </>
                ) : (
                  <div className="empty-state">
                    <p>Nie utworzono jeszcze żadnego zamówienia.</p>
                    <p>
                      Przejdź do koszyka, dodaj produkty i złóż pierwsze
                      zamówienie.
                    </p>
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
