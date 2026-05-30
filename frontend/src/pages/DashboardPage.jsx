import Navbar from "../components/Navbar";
import useCurrentOperator from "../hooks/useCurrentOperator";

function DashboardPage() {
  const { operator, authLoading, authError } = useCurrentOperator();

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
    return (
      <main className="page">
        <section className="card">
          <p className="error">{authError}</p>
        </section>
      </main>
    );
  }

  return (
    <>
      <Navbar />

      <main className="page">
        <section className="card">
          <h1>Dashboard</h1>

          <p>Zalogowany operator:</p>

          <div className="details">
            <p>
              <strong>ID:</strong> {operator.id}
            </p>

            <p>
              <strong>Email:</strong> {operator.email}
            </p>

            <p>
              <strong>Imię:</strong> {operator.first_name}
            </p>

            <p>
              <strong>Nazwisko:</strong> {operator.last_name}
            </p>

            <p>
              <strong>Aktywny:</strong>{" "}
              {operator.is_active ? "tak" : "nie"}
            </p>
          </div>
        </section>
      </main>
    </>
  );
}

export default DashboardPage;