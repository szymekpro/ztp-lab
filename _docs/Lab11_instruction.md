# Laboratorium 11
W poprzednim laboratorium została przygotowana podstawowa aplikacja frontendowa w React, która komunikuje się z backendem FastAPI. Frontend umożliwiał rejestrację i logowanie operatora, ochronę widoków wymagających sesji oraz pracę na roboczej grupie studentów.

Celem Laboratorium 11 jest rozwinięcie tego procesu o kolejne etapy: zatwierdzenie roboczej grupy, wyświetlenie historii przypisań, podejrzenie szczegółów konkretnego przypisania oraz zakończenie przypisania z poziomu interfejsu użytkownika.

## Historia przypisań operatora
W poprzednim laboratorium frontend pozwalał operatorowi pracować wyłącznie na roboczej grupie studentów. Po zatwierdzeniu draftu backend tworzył batch przypisania, jednak aplikacja nie miała jeszcze widoku, który pozwalałby podejrzeć historię utworzone przypisania ani sprawdzić ich aktualnego statusu.

Aby zaimplementować ten widok, początkowo łączymy frontend z endpointem `GET /assignments`, który zwraca listę przypisań aktualnie zalogowanego operatora. W pliku `App.js` dodajemy import:
```js
import AssignmentsPage from "./pages/AssignmentsPage";
```
Następnie dopisujemy nowy route:
```js
// frontend/src/App.js

<Route
  path="/assignments"
  element={
    <ProtectedRoute>
      <AssignmentsPage />
    </ProtectedRoute>
  }
/>
```

Do komponentu `Navbar.jsx` dodajemy nowy link:
```js
// frontend/src/components/Navbar.jsx
<Link to="/assignments">
  Przypisania
</Link>
```

Po przygotowaniu routingu oraz nawigacji możemy przejść do utworzenia właściwego widoku historii przypisań. Tworzymy nowy plik `AssignmentsPage.jsx`.
```js
// frontend/src/pages/AssignmentsPage.jsx

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { apiGet } from "../api/client";
import Navbar from "../components/Navbar";
import StatusBadge from "../components/StatusBadge";
import useCurrentOperator from "../hooks/useCurrentOperator";

function AssignmentsPage() {
  const { authLoading, authError } = useCurrentOperator();

  const [assignments, setAssignments] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function loadAssignments() {
    try {
      const data = await apiGet("/assignments");
      setAssignments(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!authLoading && !authError) {
      loadAssignments();
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
          <h1>Historia przypisań</h1>

          {loading && <p>Ładowanie przypisań...</p>}

          {error && <p className="error">{error}</p>}

          {!loading && !error && assignments.length === 0 && (
            <div className="empty-state">
              <p>Brak zatwierdzonych przypisań.</p>

              <p>
                Przejdź do roboczej grupy, dodaj studentów i zatwierdź
                przypisanie.
              </p>
            </div>
          )}

          {!loading && !error && assignments.length > 0 && (
            <div className="assignment-list">
              {assignments.map((assignment) => (
                <article key={assignment.id} className="assignment-item">
                  <div>
                    <strong>{assignment.assignment_number}</strong>

                    <p>
                      Liczba studentów: {assignment.students_count}
                    </p>

                    <p>
                      Suma ECTS: {assignment.total_ects}
                    </p>
                  </div>

                  <div className="assignment-actions">
                    <StatusBadge status={assignment.status} />

                    <Link to={`/assignments/${assignment.id}`}>
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

export default AssignmentsPage;
```

Komponent nie zakłada, że dane zawsze zostaną natychmiast poprawnie pobrane z backendu. Widok obsługuje kilka możliwych stanów aplikacji.

Pierwszym stanem jest `loading`, czyli moment, w którym request do backendu jeszcze trwa:

```js
const [loading, setLoading] = useState(true);
```
Po zakończeniu requestu, niezależnie od jego wyniku, ustawiamy:
```js
finally {
  setLoading(false);
}
```
Ten kod powoduje zakończenie stanu ładowania po wykonaniu requestu do backendu.

Sam komunikat ładowania jest renderowany w JSX:
```js
{loading && <p>Ładowanie przypisań...</p>}
```

Drugim stanem obsługiwanym przez nowy widok jest `error`, renderowany dla sytuacji w której backend zwraca błąd albo request nie powodzi się z innego powodu. 
```js
const [error, setError] = useState("");
```
Jeżeli w trakcie pobierania danych wystąpi błąd, zapisujemy jego treść w stanie komponentu:
```js
catch (err) {
  setError(err.message);
}
```
Błąd jest wyświetlany użytkownikowi:
```js
{error && <p className="error">{error}</p>}
```
Trzecim stanem jest `empty state`, czyli sytuacja, w której request zakończył się poprawnie, ale backend zwrócił pustą listę przypisań. Nie jest to błąd, tylko normalny stan aplikacji, np. gdy operator nie zatwierdził jeszcze żadnej roboczej grupy.
```js
{!loading && !error && assignments.length === 0 && (
  <div className="empty-state">
    <p>Brak zatwierdzonych przypisań.</p>

    <p>
      Przejdź do roboczej grupy, dodaj studentów i zatwierdź
      przypisanie.
    </p>
  </div>
)}
```
Dopiero gdy dane zostały pobrane poprawnie, nie ma błędu i lista nie jest pusta, renderowana jest właściwa lista przypisań:
```js
{!loading && !error && assignments.length > 0 && (
  <div className="assignment-list">
    ...
  </div>
)}
```

Każdy element listy wyświetla numer przypisania, liczbę studentów, sumę ECTS oraz aktualny status batcha. Dodatkowo użytkownik może przejść do widoku szczegółów konkretnego przypisania. Statusy przypisań są wyświetlane wykorzystując osobny komponent `StautusBadge.jsx`. 
```js
// frontend/src/components/StatusBadge.jsx

function StatusBadge({ status }) {
  const className = `status-badge status-${status.toLowerCase()}`;

  return (
    <span className={className}>
      {status}
    </span>
  );
}

export default StatusBadge;
```
Komponent dynamicznie tworzy nazwę klasy CSS na podstawie aktualnego statusu przypisania. Dzięki temu frontend może automatycznie przypisywać odpowiedni wygląd dla statusów Pending/Completed/Cancelled. Style odpowiadające za wygląd statusów zostały dopisane do pliku index.css.

## Szczegóły przypisania
Po przygotowaniu widoku historii przypisań użytkownik może przejść do listy swoich batchy, jednak nadal nie ma możliwości podejrzenia szczegółowych informacji dotyczących konkretnego przypisania. W kolejnym kroku rozszerzamy frontend o widok szczegółów pojedynczego batcha. Do frontendu integrujemy komunikację z endpointem `GET /assignments/{batchId}`, który zwraca szczegółowe informacje o wybranym przypisaniu (zamówieniu). Widok szczegółów przypisania będzie dostępny pod adresem `/assignments/:batchId`, gdzie `:batchId` oznacza dynamiczny parametr URL. Dzięki niemu jeden komponent może obsługiwać wiele adresów. 
```
/assignments/1
/assignments/2
/assignments/15
```
W celu zaimplementowania tej funkcjonalności tworzymy własciwy widok szczegółów batcha. W tym celu tworzymy plik `AssignmentDetailsPage.jsx`. W tym komponencie wykorzystujemy po raz pierwszy hook `useParams()`, pozwalający na dynamiczne pobieranie parametrów z URL. Dzięki temu komponent ma możliwość dynamicznego pobierania szczegółów różnych batchy bez konieczności tworzenia osobnego route'a dla każdego przypisania. 

Warto też zwrócić uwagę, że routing `/assignments/:batchId` nie stanowi mechanizmu autoryzacji. Użytkownik ma możliwość wpisania dowolnego id w pasku adresu przeglądarki. Właśnie dlatego backend podczas pobierania szczegółów przypisania sprawdza nie tylko `batch_id`, ale także identyfikator aktualnie zalogowanego użytkownika:
```python 
# app/group_assignment/data/assignment_repository.py
get_batch_by_id_and_operator_id(
    db=db,
    operator_id=operator_id,
    batch_id=batch_id,
)
```
Operator może dzięki temu tylko pobrać własne przypisania, nawet jeśli znałby identyfikatory innych rekordów. Tak jak w poprzednim widoku, widok `AssignmentDetailsPage.jsx` również obsługuje stany aplikacji `loading`, `error` oraz `empty state`. 

Loading jest aktywny, aż do momentu zakończenia requestu do backendu
```js
const [loading, setLoading] = useState(true);
```
Po zakończeniu requestu wykonywany jest fragment:
```js
finally {
  setLoading(false);
}
```
który kończy stan ładowania niezależnie od tego, czy request zakończył się sukcesem czy błędem.

Dla pustego przypisania frontend wyświetla:
```html
<div className="empty-state">
  <p>Brak studentów w przypisaniu.</p>
</div>
```
Natomiast poprawnie pobrane dane renderowane są dynamicznie przez
```js
assignment.items.map(...)
```

## Zatwierdzanie grupy roboczej
Po poprawnym zatwierdzeniu backend ma utworzyć nowe przypisanie ze statusem `PENDING`, a frontend przenieść operatora do widoku historii przypisań. W tym celu dodany został przycisk w widoku `DraftPage.jsx` zatwierdzający grupę roboczą. 

Do pliku `DraftPage.jsx` dodajemy import useNavigate, ponieważ po zatwierdzeniu draftu chcemy automatycznie przekierować użytkownika do `/assignments`.
```js
import { useNavigate } from "react-router-dom";
```
Wewnątrz komponentu dodajemy:
```js
const navigate = useNavigate();
```
Następnie dodajemy osobny stan odpowiedzialny za informację, czy trwa wykonywanie operacji `confirm`.
```js
const [confirmLoading, setConfirmLoading] = useState(false);
```
Pełna funkcja wygląda następująco:
```js
async function handleConfirmAssignment() {
  setError("");
  setConfirmLoading(true);

  try {
    await apiPost("/assignments/confirm", {});
    navigate("/assignments");
  } catch (err) {
    setError(err.message);
  } finally {
    setConfirmLoading(false);
  }
}
```
Funkcja najpierw czyści poprzedni komunikat błędu, następnie ustawia `confirmLoading` na **true**, aby oznaczyć rozpoczęcie requestu. Jeżeli backend poprawnie zatwierdzi draft, React przekieruje użytkownika do historii przypisań. Jeżeli wystąpi błąd, jego treść zostanie zapisana w stanie error i wyświetlona w widoku.

Przed renderowaniem widoku dodajemy również informację, czy draft jest pusty:
```js
const isDraftEmpty = !draft || draft.items.length === 0;
```
Ta wartość zostanie wykorzystana do zablokowania przycisku zatwierdzania, w przypadku gdy operator nie dodał żadnych studentów do grupy roboczej.
W części JSX pod listą studentów w drafcie dodajemy przycisk:
```js
<div className="actions-bar">
  <button
    disabled={isDraftEmpty || confirmLoading}
    onClick={handleConfirmAssignment}
  >
    {confirmLoading
      ? "Zatwierdzanie..."
      : "Zatwierdź przypisanie"}
  </button>
</div>
```

<p align="center">
    <img src="images/Lab_11/complete_button.png" width="50%">
</p>

## Complete assignment
Po zatwierdzeniu roboczej grupy backend tworzy przypisanie ze statusem PENDING. Taki status oznacza, że proces został rozpoczęty, ale nie został jeszcze zakończony. W poprzednim laboratorium operacja zakończenia przypisania została zaimplementowana po stronie backendu jako osobny command i handler. Teraz podłączamy tę operację do widoku w React. Widok zostanie rozszerzony o przycisk "Zakończ przypisanie", który będzie dostępny tylko dla przypisań o statusie **PENDING**. Po kliknięciu przycisku frontend wywołuje endpoint `POST /assignments/{batchId}/complete`. Ta operacja wymaga `Idempotency-Key`, dlatego po stronie frontendu generujemy go przed wykonaniem requestu. Wykorzystujemy do tego `crypto.randomUUID()`.

W pliku `AssignmentDetailsPage.jsx` należy rozszerzyć import z klienta API
```js
import { apiGet, apiRequest } from "../api/client";
```
Następnie w komponencie dodajemy osobne stany dla komunikatów oraz wykonywania operacji `complete`:
```js
const [message, setMessage] = useState("");
const [completeLoading, setCompleteLoading] = useState(false);
```
Funkcja odpowiedzialna za zakończenie przypisania wygląda następująco:
```js
async function handleCompleteAssignment() {
  setMessage("");
  setError("");
  setCompleteLoading(true);

  try {
    await apiRequest(`/assignments/${batchId}/complete`, {
      method: "POST",
      headers: {
        "Idempotency-Key": crypto.randomUUID(),
      },
    });

    setMessage("Przypisanie zostało zakończone.");
    await loadAssignmentDetails();
  } catch (err) {
    setError(err.message);
  } finally {
    setCompleteLoading(false);
  }
}
```
W tym fragmencie frontend wykonuje request `POST` do endpointu `POST /assignments/{batchId}/complete`, przekazując w nagłówku unikalny `Idempotency-Key`. Jeżeli operacja zakończy się poprawnie, wyświetlany jest komunikat sukcesu, a następnie ponownie pobierane są szczegóły przypisania. Dzięki temu użytkownik od razu widzi aktualny status batcha.

Dodajemy również komunikat sukcesu:
```js
{message && <p className="success">{message}</p>}
```
A pod szczegółami przypisania dodajemy przycisk wykonujący operację complete
```js
{assignment.status === "PENDING" ? (
  <div className="actions-bar">
    <button
      disabled={completeLoading}
      onClick={handleCompleteAssignment}
    >
      {completeLoading
        ? "Kończenie przypisania..."
        : "Zakończ przypisanie"}
    </button>
  </div>
) : (
  <div className="info-box">
    <p>
      To przypisanie ma status <strong>{assignment.status}</strong> i nie może
      zostać ponownie zakończone.
    </p>
  </div>
)}
```
Jeżeli przypisanie ma status `PENDING`, użytkownik widzi przycisk pozwalający zakończyć proces. Jeśli ten status jest inny, przycisk nie jest wyświetlany. Zamiast tego wyświetlana jest instrukcja, że przypisanie nie może zostać zakończone ponownie.
<p align="center">
    <img src="images/Lab_11/complete_button.png" width="50%">
</p>

## Dashboard operatora + mini BFF
Oprócz historii przypisań i widoku szczegółów batcha, aplikacja powinna wyświetlać więcej informacji w dashboardzie operatora. Dashboard zostaje rozszerzony o podsumowanie najważniejszych danych biznesowych:
* liczbę wszystkich przyspisań
* liczbę przypisań o statusie PENDING
* liczbę przypisań o statusie COMPLETED
* ostatnie przypisanie operatora.

### BFF - Backend For Frontend
Backend For Frontend, czyli BFF to wzorzec architektoniczny polegający na przygotowaniu warstwy backendowej specjalnie pod potrzeby konkretnego frontendu. Jego zadaniem nie jest zastąpienie głównej logiki systemu, ale dostarczenie frontendowi danych w takiej postaci, w jakiej są mu potrzebne do zbudowania konkretnego widoku. 

W klasycznej aplikacji frontend często składa dane z kilku endpointów i odpowiada za ich filtrowanie, przekształcanie lub wykonywanie innych zapytań aby dostosować dane do wyświetlenia w widoku. W podejściu BFF robi to za niego backendowa warstwa pośrednia. Frontend wysyła jedno żądanie, a BFF pobiera potrzebne dane z różnych części systemu, łączy je, upraszcza i zwraca dokładnie w takiej formie, jakiej potrzebuje ekran aplikacji.
Dzięki temu frontend może mieć prostszą logikę, a główny backend nie musi być projektowany pod każdy szczegół konkretnego ekranu.

W tym projekcie nie tworzymy osobnego mikroserwisu. Wprowadzamy jedynie uproszczoną wersję BFF przez endpoint `GET /assignments/dashboard/summary`. Endpoint ten przygotowuje dane biznesowe bezpośrednio do użycia w dashboardzie. Dzięki temu frontend zdobywa te informacje wykonując wyłącznie jeden request.

```python
# app/group_assignment/service/dashboard_query_service.py

from sqlalchemy.orm import Session

from app.group_assignment.data.assignment_repository import (
    get_batches_by_operator_id,
)
from app.group_assignment.model.assignment_status import AssignmentStatus


def get_dashboard_summary(
    db: Session,
    operator_id: int,
) -> dict:
    batches = get_batches_by_operator_id(
        db=db,
        operator_id=operator_id,
    )

    total_assignments = len(batches)

    pending_assignments = len(
        [
            batch
            for batch in batches
            if batch.status == AssignmentStatus.PENDING
        ]
    )

    completed_assignments = len(
        [
            batch
            for batch in batches
            if batch.status == AssignmentStatus.COMPLETED
        ]
    )

    last_assignment = batches[0] if batches else None

    return {
        "total_assignments": total_assignments,
        "pending_assignments": pending_assignments,
        "completed_assignments": completed_assignments,
        "last_assignment": last_assignment,
    }
```
Query service pobiera wszystkie przypisania operatora, a następnie przygotowuje uproszczone podsumowanie danych wykorzystywane przez dashboard.
Po przygotowaniu query service należy udostępnić nowy endpoint w pliku `group_assignment/web/routes.py`. Dodajemy import oraz nowy endpoint. 
```python
from app.group_assignment.service.dashboard_query_service import (
    get_dashboard_summary,
)
...
@router.get("/dashboard/summary")
def get_dashboard_summary_endpoint(
    operator: OperatorORM = Depends(
        get_current_operator_dependency
    ),
    db: Session = Depends(get_db),
):
    return get_dashboard_summary(
        db=db,
        operator_id=operator.id,
    )
```
Endpoint wykorzystuje identyfikator aktualnie zalogowanego operatora i zwraca dane przygotowane pod dashboard frontendu.

Mając już w pełni przygotowany endpoint, rozszerzamy podstronę `DashboardPage.jsx`. Dodajemy nowe stany:
```js
const [summary, setSummary] = useState(null);
const [summaryLoading, setSummaryLoading] = useState(true);
const [summaryError, setSummaryError] = useState("");
```
Następnie dodajemy funkcję pobierającą dane dashboardu:
```js
async function loadSummary() {
  try {
    const data = await apiGet(
      "/assignments/dashboard/summary"
    );

    setSummary(data);
  } catch (err) {
    setSummaryError(err.message);
  } finally {
    setSummaryLoading(false);
  }
}
```
oraz wywołujemy ją w useEffect():
```js
useEffect(() => {
  async function loadDashboard() {
    await loadSummary();
  }

  if (!authLoading && !authError) {
    loadDashboard();
  }
}, [authLoading, authError]);
```
Na samym końcu modyfikujemy JSX dashboardu
```js
{summaryLoading && (
  <p>Ładowanie podsumowania...</p>
)}

{summaryError && (
  <p className="error">{summaryError}</p>
)}

{!summaryLoading && !summaryError && summary && (
  <>
    <div className="summary-grid">
      <div className="summary-card">
        <span>Wszystkie przypisania</span>

        <strong>
          {summary.total_assignments}
        </strong>
      </div>

      <div className="summary-card">
        <span>Oczekujące</span>

        <strong>
          {summary.pending_assignments}
        </strong>
      </div>

      <div className="summary-card">
        <span>Zakończone</span>

        <strong>
          {summary.completed_assignments}
        </strong>
      </div>
    </div>

    <div className="last-assignment">
      <h2>Ostatnie przypisanie</h2>

      {summary.last_assignment ? (
        <>
          <p>
            <strong>Numer:</strong>
            {" "}
            {summary.last_assignment.assignment_number}
          </p>

          <p>
            <strong>Status:</strong>
            {" "}
            <StatusBadge
              status={summary.last_assignment.status}
            />
          </p>

          <p>
            <strong>Liczba studentów:</strong>
            {" "}
            {summary.last_assignment.students_count}
          </p>

          <p>
            <strong>Suma ECTS:</strong>
            {" "}
            {summary.last_assignment.total_ects}
          </p>

          <Link
            to={`/assignments/${summary.last_assignment.id}`}
          >
            Zobacz szczegóły
          </Link>
        </>
      ) : (
        <p>
          Nie utworzono jeszcze żadnego przypisania.
        </p>
      )}
    </div>
  </>
)}
```

## BONUS - Powiadomienia toast oraz poprawa UX 
Dotychczasowo frontend wyświetlał komunikaty sukcesu lub błędów bezpośrednio w widoku strony wykorzystując `<p className="success/error">...</p>`. Takie podejście jest poprawne, jednak w nowoczesnych aplikacjach często wykorzystuje się tzw **toast notifications**. Są to niewielkie komunikaty pojawiające się w rogu aplikacji (najczęściej w prawym górnym rogu) i znikające po chwili. Dzięki temu użytkownik od razu zwraca uwagę na wyskakujący wynik operacji bez konieczności doszukiwania się tego komunikatu w treści strony. Aby zaimplementować powiadomienia toast, rozszerzamy frontend o bibliotekę `react-toastify`. 

Instalację tej biblioteki wykonujemy poleceniem `npm install react-toastify` będąc w folderze `frontend/`. Po zainstalowaniu biblioteki należy skonfigurować globalny kontener odpowiedzialny za renderowanie powiadomień toast. W pliku `App.js` dodajemy importy:
```js
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
```
Następnie wewnątrz `<BrowserRouter>` dodajemy
```js
<ToastContainer
  position="top-right"
  autoClose={3000}
/>
```
Kontener odpowiada za renderowanie **wszystkich** toastów wyświetlanych w aplikacji. Dzięki temu komunikaty mogą być wywoływane z dowolnego komponentu React. Po skonfigurowaniu `ToastContainer` możemy rozszerzyć wybrane widoki aplikacji. 

W pliku `DraftPage.jsx` dodajemy odpowiedni import oraz rozszerzamy funkcję usuwania studenta z draftu:
```js
import { toast } from "react-toastify";
...
async function handleRemoveItem(itemId) {
  setMessage("");
  setError("");

  try {
    await apiDelete(
      `/assignments/draft/items/${itemId}`
    );

    toast.success(
      "Student został usunięty z roboczej grupy."
    );

    await loadDraft();
  } catch (err) {
    setError(err.message);

    toast.error(err.message);
  }
}
```
Po poprawnym wykonaniu operacji użytkownik zobaczy komunikat sukcesu w prawym górnym rogu aplikacji. Jeżeli request zakończy się błędem, frontend wyświetli toast błędu zawierający komunikat zwrócony przez backend. W analogiczny sposób rozszerzamy operację zatwierdzenia draftu. 

Korzystając z toastify rozszerzamy również widok AssignmentDetailsPage.jsx. Dodajemy import oraz modyfikujemy funkcję `handleCompleteAssignment()`.
```js
async function handleCompleteAssignment() {
  setMessage("");
  setError("");
  setCompleteLoading(true);

  try {
    await apiRequest(
      `/assignments/${batchId}/complete`,
      {
        method: "POST",
        headers: {
          "Idempotency-Key":
            crypto.randomUUID(),
        },
      }
    );

    toast.success(
      "Przypisanie zostało zakończone."
    );

    await loadAssignmentDetails();
  } catch (err) {
    setError(err.message);

    toast.error(err.message);
  } finally {
    setCompleteLoading(false);
  }
}
```
Dzięki wykorzystaniu toastów użytkownik otrzymuje natychmiastową informację o wyniku wykonywanej operacji bez konieczności analizowania całej zawartości strony.

## Zadanie do wykonania na laboratorium
W ramach laboratorium należy uruchomić backend oraz frontend projektu, sprawdzić komunikację pomiędzy React i FastAPI, a następnie przejść przez podstawowy proces użytkownika w aplikacji.
Wykonaj poniższe kroki:
1. Aktywuj środowisko wirtualne backendu:<br>
  `.venv\Scripts\activate`
2. Uruchom kontenery projektu za pomocą polecenia:<br>
  `docker compose up -d --build`
3. Uruchom backend FastAPI poleceniem:<br>
  `uvicorn main:app --reload`
4. W osobnym terminalu, wejdź do folderu frontend i uruchom frontend React:
  `cd frontend`
  `npm start`
5. Frontend powinien być dostępny pod adresem:<br>
  `http://localhost:3000`
6. Zaloguj się do aplikacji jako operator.
7. Dodaj studentów do roboczej grupy i sprawdź:
* aktualizację liczby studentów,
* sumę ECTS,
* usuwanie studentów z draftu,
* działanie toast notifications.
8. Zatwierdź roboczą grupę przyciskiem Zatwierdź przypisanie, a następnie sprawdź, czy aplikacja przechodzi do widoku `/assignments`.
9. W widoku historii przypisań sprawdź, czy pojawił się nowy batch ze statusem `PENDING` oraz czy działa przejście do szczegółów.
10. W szczegółach batcha kliknij `Zakończ przypisanie` i sprawdź, czy status zmienia się na `COMPLETED`, a przycisk znika.
11. Wróć do dashboardu i sprawdź, czy zaktualizowały się liczby przypisań oraz sekcja ostatniego przypisania.

## Projekt 4. Etap 2. 
1. Rozszerzenie aplikacji frontendowej o historię zamówień oraz widok szczegółów zamówienia. Aplikacja powinna umożliwiać wyświetlenie listy zamówień aktualnie zalogowanego użytkownika wraz ze statusem zamówienia, liczbą produktów oraz sumą zamówienia. Użytkownik powinien mieć możliwość przejścia do szczegółów konkretnego zamówienia przy pomocy dynamicznego routingu /orders/:orderId. Widok szczegółów powinien prezentować pełną zawartość zamówienia oraz aktualny status procesu biznesowego.
2. Implementacja procesu zakończenia zamówienia po stronie frontendowej. Użytkownik powinien mieć możliwość wykonania operacji `complete order` z poziomu Reacta. Frontend powinien wykonywać request `POST /orders/{orderId}/complete`, przekazywać `Idempotency-Key`, odświeżać dane zamówienia po zakończeniu operacji oraz odpowiednio reagować na statusy biznesowe `PENDING`, `COMPLETED` oraz `CANCELLED`. Operacja zakończenia zamówienia nie powinna być dostępna dla zamówień już zakończonych lub anulowanych.
3. Rozszerzenie dashboardu użytkownika o podsumowanie danych biznesowych. Należy przygotować dedykowany endpoint dashboardowy zwracający zagregowane informacje dotyczące zamówień użytkownika, np. liczbę wszystkich zamówień, liczbę zamówień oczekujących, liczbę zamówień zakończonych oraz ostatnie zamówienie użytkownika. Frontend powinien wyświetlać te dane w postaci prostego dashboardu oraz poprawnie obsługiwać loading state, error state oraz empty state.
