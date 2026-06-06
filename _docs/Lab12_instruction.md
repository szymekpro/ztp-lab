# Laboratorium 12
W poprzednim laboratorium aplikacja została rozszerzona o historię przypisań, widok szczegółów batcha, obsługę statusów biznesowych oraz rozwinięty dashboard operatora. Użytkownik może obecnie przejść przez pełny proces przypisania studentów od utworzenia roboczej grupy aż do zakończenia procesu.

## Komponenty LoadingState, ErrorState, EmptyState
W poprzednich laboratoriach w wielu komponentach React pojawiały się podobne fragmenty kodu odpowiedzialne za wyświetlanie komunikatów ładowania danych, błędów oraz pustych wyników.Przykładowo w poszczególnych widokach wielokrotnie występowały konstrukcje podobne do:

```js
{loading && <p>Ładowanie danych...</p>}

{error && <p className="error">{error}</p>}

//oraz:

{items.length === 0 && (
  <div className="empty-state">
    <p>Brak danych.</p>
  </div>
)}
```

Takie podejście jest poprawne, jednak wraz ze wzrostem liczby widoków prowadzi do powielania bardzo podobnej logiki w wielu miejscach aplikacji. W praktyce frontendowej często stosuje się wydzielanie często używanych fragmentów interfejsu do osobnych komponentów wielokrotnego użytku. W związku z tym tworzymy trzy nowe komponenty: `LoadingState.jsx`, `ErrorState.jsx`, `EmptyState.jsx`. Komponenty te będą odpowiadały za prezentację najczęściej występujących stanów aplikacji. Dzięki temu kolejne widoki będą mogły korzystać ze wspólnego rozwiązania zamiast implementować własne komunikaty ładowania, błędów oraz pustych wyników.

```js
// frontend/src/components/LoadingState.jsx
function LoadingState({ message = "Ładowanie danych..." }) {
  return (
    <div className="state-box">
      <p>{message}</p>
    </div>
  );
}

export default LoadingState;
```
Komponent przyjmuje opcjonalny parametr `message`, dzięki czemu różne widoki mogą wyświetlać własne komunikaty bez konieczności tworzenia kolejnych wersji komponentu.

Następnie tworzymy plik `ErrorState.jsx`:
```js
// frontend/src/components/ErrorState.jsx
function ErrorState({ message = "Wystąpił błąd." }) {
  return (
    <div className="state-box error-box">
      <p>{message}</p>
    </div>
  );
}

export default ErrorState;
```
Komponent odpowiada za prezentację błędów zwracanych przez backend lub błędów powstałych podczas wykonywania requestów HTTP.

Ostatnim komponentem jest widok pustych danych. Tworzymy plik `EmptyState.jsx`.
```js
// frontend/src/components/EmptyState.jsx
function EmptyState({ title, description }) {
  return (
    <div className="empty-state">
      <p>
        <strong>{title}</strong>
      </p>

      {description && (
        <p>
          {description}
        </p>
      )}
    </div>
  );
}

export default EmptyState;
```

Po utworzeniu komponentów `LoadingState`, `ErrorState` oraz Empty`State możemy uprościć istniejące widoki aplikacji. Zamiast powtarzać w wielu plikach podobne fragmenty JSX:
```js
{loading && <p>Ładowanie przypisań...</p>}

{error && <p className="error">{error}</p>}
```
możemy używać wspólnych komponentów:
```js
{loading && (
  <LoadingState message="Ładowanie przypisań..." />
)}

{error && (
  <ErrorState message={error} />
)}
```
Analogicznie pusty stan widoku można zapisać przez `EmptyState`:
```js
<EmptyState
  title="Brak zatwierdzonych przypisań."
  description="Przejdź do roboczej grupy, dodaj studentów i zatwierdź przypisanie."
/>
```
Taka zmiana nie dodaje nowej funkcjonalności, ale porządkuje kod. Widoki stają się krótsze, a sposób prezentowania ładowania, błędów i pustych danych jest utrzymywany w jednym miejscu.

## Walidacja formularza rejestracji
Do tej pory formularz rejestracji przekazywał dane bezpośrednio do backendu. Oznaczało to, że nawet oczywiste błędy, takie jak pozostawienie pustego pola lub wpisanie niepoprawnego adresu email, były wykrywane dopiero po wykonaniu requestu HTTP. W praktyce aplikacje frontendowe powinny wykonywać część walidacji jeszcze przed wysłaniem danych do serwera. Takie podejście poprawia komfort użytkowania aplikacji oraz ogranicza liczbę niepotrzebnych requestów wykonywanych do backendu.

W naszym rozwiązaniu poszerzamy formularz rejestracji o podstawową walidację sprawdzającą:
* czy wszystkie pola zostały uzupełnione,
* czy adres email ma poprawny format,
* czy hasło posiada minimalną długość,
* czy pola hasła i potwierdzenia hasła zawierają identyczne wartości.

W pliku `RegisterPage.jsx`, przed funkcją `handleSubmit()` dodajemy funkcję odpowiedzialną za walidację formularza:

```js
function validateForm() {
    if (!firstName.trim()) {
        return "Imię jest wymagane.";
    }

    if (!lastName.trim()) {
        return "Nazwisko jest wymagane.";
    }

    if (!email.trim()) {
        return "Email jest wymagany.";
    }

    const emailRegex = /\S+@\S+\.\S+/;

    if (!emailRegex.test(email)) {
        return "Niepoprawny adres email.";
    }

    if (password.length < 8) {
        return "Hasło musi mieć co najmniej 8 znaków.";
    }

    if (password !== confirmPassword) {
        return "Hasła nie są identyczne.";
    }

    return null;
}
```
Funkcja zwraca komunikat błędu w przypadku wykrycia niepoprawnych danych lub wartość `null`, gdy wszystkie pola spełniają wymagania walidacyjne.

Następnie rozszerzamy początek funkcji `handleSubmit()`:
```js
async function handleSubmit(event) {
    event.preventDefault();

    setError("");

    const validationError = validateForm();

    if (validationError) {
        setError(validationError);
        return;
    }

    setLoading(true);

    ...
}
```
Przed wykonaniem requestu React wywołuje funkcję `validateForm()`. Jeżeli zostanie zwrócony komunikat błędu, zostanie on zapisany w stanie komponentu i wyświetlony użytkownikowi. W takiej sytuacji request do backendu nie zostanie wykonany. Warto zwrócić uwagę, że walidacja frontendowa nie zastępuje walidacji backendowej. Backend nadal powinien weryfikować poprawność wszystkich danych, ponieważ użytkownik może pominąć frontend i wysłać request bezpośrednio do API. 

# Walidacja formularza logowania
Podobnie jak w przypadku formularza rejestracji, również ekran logowania może wykonywać podstawową walidację przed wysłaniem danych do backendu. W przypadku logowania sprawdzimy, czy użytkownik podał adres email, czy adres posiada poprawny format oraz czy uzupełnione zostało pole hasła.

W pliku `LoginPage.jsx` funkcję odpowiedzialną za walidację formularza:
```js
function validateForm() {
  if (!email.trim()) {
    return "Email jest wymagany.";
  }

  const emailRegex = /\S+@\S+\.\S+/;

  if (!emailRegex.test(email)) {
    return "Niepoprawny adres email.";
  }

  if (!password.trim()) {
    return "Hasło jest wymagane.";
  }

  return null;
}
```
Następnie rozszerzamy początek funkcji handleSubmit():
```js
async function handleSubmit(event) {
  event.preventDefault();

  setError("");

  const validationError = validateForm();

  if (validationError) {
    setError(validationError);
    return;
  }

  setLoading(true);

  ...
}
```
Po wprowadzeniu tych zmian oba formularze odpowiedzialne za autentykację użytkownika wykorzystują podobny mechanizm walidacji. Dzięki temu aplikacja zachowuje się bardziej przewidywalnie, a użytkownik otrzymuje natychmiastową informację zwrotną o niepoprawnie wprowadzonych danych.

## Anulowanie przypisania
Dodanie anulowania przypisania pozwala domknąć obsługę maszyny stanów również po stronie interfejsu użytkownika. Operator będzie mógł zakończyć proces pozytywnie przez complete albo anulować go, jeżeli przypisanie nie powinno być dalej przetwarzane.

Po stronie backendu dodajemy osobny `command` odpowiedzialny za operację anulowania. Tworzymy plik `cancel_assignment_command.py`.

```python
# app/group_assignment/service/cancel_assignment_command.py
class CancelAssignmentCommand:
    command_name = "CancelAssignmentCommand"

    def __init__(
        self,
        operator_id: int,
        batch_id: int,
        reason: str | None = None,
    ):
        self.operator_id = operator_id
        self.batch_id = batch_id
        self.reason = reason
```
Command przechowuje dane potrzebne do wykonania operacji anulowania przypisania. W naszym przypadku najważniejsze są `operator_id` oraz `batch_id`, ponieważ anulowanie powinno być wykonywane wyłącznie na przypisaniu należącym do aktualnie zalogowanego operatora.

Do commanda tworzymy również handler:
```python
# app/group_assignment/service/cancel_assignment_handler.py
from sqlalchemy.orm import Session
from app.group_assignment.data.assignment_repository import get_batch_by_id_and_operator_id, save_assignment_batch
from app.group_assignment.model.assignment_schema import AssignmentBatchResponse
from app.group_assignment.model.assignment_status import AssignmentStatus
from app.group_assignment.service.assignment_exceptions import AssignmentNotFoundError
from app.group_assignment.service.assignment_state_machine import validate_status_transition
from app.group_assignment.service.cancel_assignment_command import CancelAssignmentCommand


def handle_cancel_assignment(
    db: Session,
    command: CancelAssignmentCommand,
) -> AssignmentBatchResponse:
    batch = get_batch_by_id_and_operator_id(
        db=db,
        batch_id=command.batch_id,
        operator_id=command.operator_id,
    )

    if batch is None:
        raise AssignmentNotFoundError("Zatwierdzone przypisanie nie istnieje.")

    validate_status_transition(
        current_status=batch.status,
        new_status=AssignmentStatus.CANCELLED,
    )
    batch.status = AssignmentStatus.CANCELLED
    batch = save_assignment_batch(db, batch)

    return AssignmentBatchResponse.model_validate(batch)
```

Handler pobiera batch na podstawie `batch_id` oraz `operator_id`, dzięki czemu operator nie może anulować przypisania należącego do innego użytkownika. Następnie wykorzystywana jest wcześniej przygotowana maszyna stanów. Funkcja `validate_status_transition()` sprawdza, czy przejście z aktualnego statusu do `CANCELLED` jest dozwolone. Jeżeli batch ma już status `COMPLETED` albo `CANCELLED`, operacja zostanie zablokowana.

Po przygotowaniu commandu i handlera udostępniamy endpoint w pliku `routes.py`.
```python
#app/group_assignment/web/routes.py
from app.group_assignment.service.cancel_assignment_command import CancelAssignmentCommand
from app.group_assignment.service.cancel_assignment_handler import handle_cancel_assignment

...

@router.post(
    "/{batch_id}/cancel",
    response_model=AssignmentBatchResponse,
    status_code=status.HTTP_200_OK,
)
def cancel_assignment_endpoint(
    batch_id: int = Path(..., gt=0),
    operator: OperatorORM = Depends(get_current_operator_dependency),
    db: Session = Depends(get_db),
):
    command = CancelAssignmentCommand(
        operator_id=operator.id,
        batch_id=batch_id,
        reason="Przypisanie anulowane przez operatora.",
    )

    try:
        return handle_cancel_assignment(
            db=db,
            command=command,
        )

    except AssignmentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except AssignmentValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

Endpoint działa analogicznie do dodanej we wcześniejszych laboratoriach operacji `/complete`. Zgodnie z zasadami przyjętymi na laboratoriach najpierw tworzony jest command, a właściwa logika zmiany statusu znajduje się w handlerze. Dzięki temu endpoint nie zawiera logiki biznesowej, tylko przekazuje żądanie do odpowiedniej warstwy aplikacji.

W pliku `AssignmentDetailsPage.jsx` dodajemy równiez osobny stan dla operacji anulowania: `const [cancelLoading, setCancelLoading] = useState(false);`. Dodajemy również funkcję odpowiedzialną za wykonanie requestu do backendu:

```js
//frontend/src/pages/AssignmentDetailsPage.jsx
  async function handleCancelAssignment() {
    const confirmed = window.confirm(
      "Czy na pewno chcesz anulować to przypisanie?"
    );

    if (!confirmed) {
      return;
    }

    setActionError("");
    setCancelLoading(true);

    try {
      await apiRequest(`/assignments/${batchId}/cancel`, {
        method: "POST",
      });

      toast.success("Przypisanie zostało anulowane.");
      await loadAssignmentDetails();
    } catch (err) {
      setActionError(err.message);
      toast.error(err.message);
    } finally {
      setCancelLoading(false);
    }
  }
```

Przed finalnym wykonaniem requestu pojawia się proste potwierdzenie przez `window.confirm()`. Jeżeli użytkownik wybierze Anuluj, funkcja zakończy działanie i request do backendu nie zostanie wykonany. To prosta forma zabezpieczenia przed przypadkowym wykonaniem operacji zmieniającej status batcha. 

## Rozszerzenie dashboardu operatora
Po dodaniu obsługi anulowania przypisania dashboard powinien uwzględniać również status `CANCELLED`. W poprzedniej wersji dashboard pokazywał liczbę wszystkich przypisań, liczbę przypisań oczekujących oraz zakończonych. Teraz proces biznesowy może zakończyć się także anulowaniem, dlatego warto pokazać tę informację również w podsumowaniu operatora.

Rozszerzymy istniejący endpointtak, aby zwracał dodatkowo liczbę anulowanych przypisań oraz listę ostatnich batchy. Dzięki temu dashboard będzie pełniejszy i lepiej pokaże aktualny stan pracy operatora. 
```python
# app/group_assignment/service/dashboard_query_service.py
from sqlalchemy.orm import Session
from app.group_assignment.data.assignment_repository import get_batches_by_operator_id
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

    cancelled_assignments = len(
        [
            batch
            for batch in batches
            if batch.status == AssignmentStatus.CANCELLED
        ]
    )

    last_assignment = batches[0] if batches else None

    recent_assignments = batches[:5]

    return {
        "total_assignments": total_assignments,
        "pending_assignments": pending_assignments,
        "completed_assignments": completed_assignments,
        "cancelled_assignments": cancelled_assignments,
        "last_assignment": last_assignment,
        "recent_assignments": recent_assignments,
    }
```

W tej wersji query service nadal pobiera przypisania należące do aktualnie zalogowanego operatora, ale oprócz dotychczasowych wartości oblicza również liczbę batchy ze statusem `CANCELLED`. Dodatkowo przygotowuje listę ostatnich pięciu przypisań. 

Aby obsłużyć nowe dane pobierane z endpointu należy zmodyfikowac również widok frontendu. Fragment odpowiedzialny za karty statystyk wygląda następująco:
```js
// frontend/src/pages/DashboardPage.jsx
<div className="summary-grid">
    <div className="summary-card">
        <span>Wszystkie przypisania</span>
        <strong>{summary.total_assignments}</strong>
    </div>

    <div className="summary-card">
        <span>Oczekujące</span>
        <strong>{summary.pending_assignments}</strong>
    </div>

    <div className="summary-card">
        <span>Zakończone</span>
        <strong>{summary.completed_assignments}</strong>
    </div>

    <div className="summary-card">
        <span>Anulowane</span>
        <strong>{summary.cancelled_assignments}</strong>
    </div>
</div>
```

Dodajemy również sekcję ostatnich przypisań. Dzięki temu użytkownik po wejściu na dashboard widzi nie tylko liczby, ale również konkretne ostatnie procesy, do których może szybko wrócić.
```js
// frontend/src/pages/DashboardPage.jsx
<div className="recent-assignments">
    <h2>Ostatnie przypisania</h2>

    {summary.recent_assignments.length === 0 ? (
        <EmptyState
        title="Brak ostatnich przypisań."
        description="Historia ostatnich przypisań pojawi się po zatwierdzeniu roboczej grupy."
        />
    ) : (
        <div className="assignment-list">
        {summary.recent_assignments.map((assignment) => (
            <article
            key={assignment.id}
            className="assignment-item"
            >
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
</div>
```
W tej sekcji ponownie wykorzystujemy komponent `StatusBadge`, dzięki czemu statusy w dashboardzie wyglądają tak samo jak w historii przypisań i w szczegółach batcha. Dodatkowo każdy element listy posiada link prowadzący do szczegółów konkretnego przypisania.

## Zadanie do wykonania na laboratorium
Wykonaj poniższe kroki:
1. Aktywuj środowisko wirtualne backendu: `.venv\Scripts\activate`
2. Uruchom kontenery projektu za pomocą polecenia: `docker compose up -d --build`
3. Uruchom backend FastAPI poleceniem: `uvicorn main:app --reload`
4. W osobnym terminalu przejdź do folderu frontend i uruchom aplikację React: `cd frontend`
`npm start`
5. Frontend powinien być dostępny pod adresem: http://localhost:3000
6. Dodaj studentów do roboczej grupy i sprawdź blokadę ponownego dodania tego samego studenta.
7. Zatwierdź przypisanie i sprawdź, czy nowy batch pojawia się w historii ze statusem `PENDING`.
8.  Przejdź do szczegółów przypisania i sprawdź działanie operacji `COMPLETED` oraz `CANCELLED`.
9.  Zweryfikuj, czy po zmianie statusu przyciski zmiany statusu nie są już dostępne.
10. Sprawdź działanie rozszerzonego dashboardu, w szczególności liczniki statusów oraz listę ostatnich przypisań.
11. Zweryfikuj działanie komponentów LoadingState

## Projekt 4. Etap 3. 
1. Rozszerzenie formularzy autentykacji o walidację frontendową. Formularze rejestracji i logowania powinny sprawdzać poprawność danych przed wysłaniem requestu do backendu. Należy zweryfikować wymagane pola, poprawność adresu email oraz zgodność haseł podczas rejestracji. W przypadku błędnych danych użytkownik powinien otrzymać odpowiedni komunikat bez wykonywania requestu HTTP.
2. Rozszerzenie procesu obsługi zamówienia o możliwość anulowania zamówienia. Użytkownik powinien mieć możliwość wykonania operacji cancel order dla zamówień znajdujących się w statusie `PENDING`. Frontend powinien wykonywać request `POST /orders/{orderId}/cancel`, odświeżać dane zamówienia po wykonaniu operacji oraz poprawnie obsługiwać statusy `PENDING`, `COMPLETED` i `CANCELLED`. Operacja anulowania nie powinna być dostępna dla zamówień zakończonych lub wcześniej anulowanych.
3. Rozszerzenie dashboardu użytkownika oraz poprawa obsługi stanów aplikacji. Dashboard powinien prezentować liczbę wszystkich zamówień, liczbę zamówień oczekujących, zakończonych i anulowanych oraz listę ostatnich zamówień użytkownika. Widoki aplikacji powinny wykorzystywać wspólne komponenty odpowiedzialne za obsługę loading state, error state oraz empty state.