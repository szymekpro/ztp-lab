import useCurrentOperator from "../hooks/useCurrentOperator";

function ProtectedRoute({ children }) {
  const { authLoading, authError } = useCurrentOperator();

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

  return children;
}

export default ProtectedRoute;