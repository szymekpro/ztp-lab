# Laboratorium 9
Celem Laboratorium 9 jest domknięcie procesu biznesowego rozpoczętego w poprzednim laboratorium oraz rozwinięcie architektury backendowej o mechanizmy wykorzystywane w rzeczywistych systemach backendowych.

W Laboratorium 8 system został rozszerzony o mechanizm roboczych grup studentów (draft) oraz proces zatwierdzania przypisania (confirm). W ramach Laboratorium 9 proces zostaje rozwinięty o bardziej rozwinięty Command Pattern, wprowadzenie do CQRS, powtórzenie ze state machine, idempotencję operacji oraz integrację z modułem notifications. Operator będzie mógł zakończyć przypisanie studentów poprzez operację complete (odpowiednik zakończenia zamówienia przez dostarczenie produktu).

## Rozwinięcie Command Pattern
W poprzednim laboratorium wprowadzony został uproszczony mechanizm `Command Pattern`. Command pełnił wtedy głównie rolę prostego obiektu przechowującego dane potrzebne do wykonania operacji. Przykładowo podczas zatwierdzania draftu wykorzystywany był command:
```python
# app/group_assignment/service/confirm_assignment_command.py
ConfirmAssignmentCommand(
    operator_id=operator.id,
)
```
w praktyce taka operacja mogła być wykonana zwykłą funkcją:
```python
confirm_assignment(operator_id)
```
W prostych aplikacjach jest to całkowicie poprawne podejście. Problem pojawia się jednak w momencie, gdy operacja zaczyna się rozrastać i wymaga coraz większej liczby parametrów oraz dodatkowych zachowań systemu.W tym laboratorium operacja `complete` nie polega już wyłącznie na zmianie jednego pola w bazie danych. System sprawdza poprawność statusu, weryfikuje idempotencję, zapisuje wykonany command oraz tworzy powiadomienia EMAIL i PUSH.

Dlatego wprowadzamy bardziej rozbudowany command:
```python
# app/group_assignment/service/complete_assignment_command.py

class CompleteAssignmentCommand:
    command_name = "CompleteAssignmentCommand"

    def __init__(
        self,
        operator_id: int,
        batch_id: int,
        idempotency_key: str,
        completed_by: str,
        source: str = "API",
        notify_email: bool = True,
        notify_push: bool = True,
        note: str | None = None,
    ):
        self.operator_id = operator_id
        self.batch_id = batch_id
        self.idempotency_key = idempotency_key
        self.completed_by = completed_by
        self.source = source
        self.notify_email = notify_email
        self.notify_push = notify_push
        self.note = note
```
Dzięki temu zamiast przekazywania wielu nieczytelnych parametrów, operacja jest przekazywana jako jeden spójny obiekt.Poprawia to czytelność kodu i ułatwia dalszy rozwój aplikacji. Rozwijając dalej aplikację możemy bezpośrednio rozszerzyć command o kolejne pola, zamiast rozbudowywać listę argumentów funkcji. W naszym projekcie mimo wszystko wykorzystujemy wersję uproszczoną `Command Pattern`. Nie stosujemy elementów takich jak `Command Bus` ale warto o nich wspomnieć. 

`Command Bus` to dodatkowa warstwa pośrednicząca między commandem a handlerem. Jego zadaniem jest odnajdywanie odpowiedniego handlera dla danego commanda. W większych aplikacjach mogłoby to wyglądać np. w taki sposób:
```python
command_bus.dispatch(command)
```
Wtedy system sam odnajduje właściwy handler i wykonuje odpowiednią operację. W naszym projekcie nie jest to jeszcze potrzebne, ponieważ liczba commandów jest niewielka i bezpośrednie wywołanie handlera pozostaje prostsze oraz bardziej czytelne.

## CQRS
W tym laboratorium wprowadzamy również `CQRS` (Command Query Responsibility Segregation). `CQRS` jest podejściem architektonicznym polegającym na rozdzieleniu operacji na te odczytujące dane (Query) oraz operacje modyfikujące stan systemu (Command).

Podejście to stosowane jest głównie w większych systemach backendowych, w których operacje odczytowe i zapisujące zaczynają znacząco się od siebie różnić. Odczyt danych często wymaga przygotowania wygodnych odpowiedzi dopasowanych pod frontend, natomiast operacje zapisujące skupiają się na walidacji procesu, zmianie statusów czy wykonywaniu bardziej złożonych operacji systemowych. W klasycznych prostych aplikacjach (jak nasz projekt do tej pory) oba typy operacji znajdują się w jednym serwisie. Wraz ze wzrostem projektu zaczyna to jednak prowadzić do sytuacji, w której jeden plik odpowiada jednocześnie za zbyt dużą ilość operacji jednocześnie.

W naszym projekcie nie implementujemy pełnej infrastruktury CQRS znanej z dużych systemów enterprise. Takie implementacje bardzo często wykorzystują dużą liczbę dodatkowych warstw i plików, takich jak osobne DTO, registry, dispatchery czy mappery. Celem laboratorium jest pokazanie najważniejszej idei tego podejścia bez nadmiernego komplikowania projektu.

Skupiamy się przede wszystkim na rozdzieleniu odpowiedzialności pomiędzy operacje odczytowe oraz operacje modyfikujące stan systemu. Takie podejście dobrze wpisuje się również w zasadę `Single Responsibility Principle`. Query service odpowiada wyłącznie za pobieranie danych, natomiast commandy i handlery odpowiadają za wykonywanie operacji zmieniających stan aplikacji. Dzięki temu kod staje się bardziej uporządkowany oraz łatwiejszy do rozwijania.

Endpointy typu POST wykorzystują commandy i handlery: `POST → command → handler → zmiana stanu systemu`

Natomiast endpointy typu GET korzystają z osobnego query service: `GET → query service → odczyt danych`

Do pliku `assignment_query_service.py`przeniesiona została logika odpowiedzialna za pobieranie historii przypisań oraz szczegółów batcha.
```python
# app/group_assignment/service/assignment_query_service.py

def list_assignment_batches(
    db: Session,
    operator_id: int,
) -> list[AssignmentBatchListItemResponse]:

def get_assignment_batch_details(
    db: Session,
    operator_id: int,
    batch_id: int,
) -> AssignmentBatchResponse:
```
Funkcje te odpowiadają wyłącznie za pobieranie danych i nie wykonują żadnych zmian w systemie. Dzięki temu struktura projektu staje się bardziej czytelna, ponieważ operacje modyfikujące stan systemu znajdują się w handlerach commandów, natomiast operacje odczytowe w query service.

## State Machine
Wspomniane w laboratorium 4 state machine odnajduje swoje zastosowanie również na obecnym etapie projektu. Dla procesu przypisania studentów dodajemy trzy statusy: `PENDING`, `COMPLETED`, `CANCELLED`.
Dozwolone są przejścia: `PENDING → COMPLETED`, `PENDING → CANCELLED`. Statusy `COMPLETED` i `CANCELLED` są uznawane jako stany końcowe. Aby to osiągnąć dodajemy:

```python
# app/group_assignment/service/assignment_state_machine.py

ALLOWED_STATUS_TRANSITIONS = {
    AssignmentStatus.PENDING: {
        AssignmentStatus.COMPLETED,
        AssignmentStatus.CANCELLED,
    },
    AssignmentStatus.COMPLETED: set(),
    AssignmentStatus.CANCELLED: set(),
}

def validate_status_transition(
    current_status: str,
    new_status: str,
) -> None:
```

## Idempotencja
Mechanizm idempotencji został już częściowo wprowadzony w Laboratorium 6 podczas implementacji modułu notifications. W tym laboratorium wprowadzamy więc idempotencję na poziomie commandów. Tabela przechowuje informacje o commandach, które zostały już wcześniej wykonane przez system.

```sql
-- app/db/init/005_processed_commands.sql

CREATE TABLE IF NOT EXISTS processed_commands (
    id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    command_name VARCHAR NOT NULL,
    idempotency_key VARCHAR NOT NULL,
    operator_id INTEGER NOT NULL REFERENCES operators(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_processed_command_key
        UNIQUE (command_name, idempotency_key)
);
```
Dodajemy również model ORM i funkcje repozytorium odpowiedzialne za sprawdzanie wykonanych commandów. Jeżeli system wykryje, że dany command został już wcześniej wykonany, operacja nie zostanie wykonana ponownie. Dzięki temu aplikacja nie zmieni drugi raz statusu przypisania, nie zapisze kolejnego processed_command oraz nie utworzy kolejnych notyfikacji EMAIL i PUSH. Jest to ważny mechanizm wykorzystywany szczególnie podczas obsługi płatności lub zamówień.

## Zakończenie przypisania
Główną operacją dodawaną w Laboratorium 9 jest endpoint `complete`, którego zadaniem jest zakończenie procesu przypisania studentów (odpowiednik zakończenia realizacji zamówienia).
Operator może wykonać operację `complete`, która sprawdza poprawność przejścia statusu, weryfikuje idempotencję, zapisuje wykonany command oraz wywołuje utworzenie powiadomienia EMAIL i PUSH. 
W tym celu dodajemy nowy command:
```python
# app/group_assignment/service/complete_assignment_command.py

class CompleteAssignmentCommand:
    command_name = "CompleteAssignmentCommand"

    def __init__(
        self,
        operator_id: int,
        batch_id: int,
        idempotency_key: str,
        completed_by: str,
        source: str = "API",
        notify_email: bool = True,
        notify_push: bool = True,
        note: str | None = None,
    ):
```
Command przechowuje wszystkie informacje potrzebne do wykonania operacji zakończenia przypisania (realizacji zamówienia). 

Następnie dodajemy handler odpowiadający za wykonanie całego procesu
```python
# app/group_assignment/service/complete_assignment_handler.py

def handle_complete_assignment(
    db: Session,
    command: CompleteAssignmentCommand,
) -> AssignmentBatchResponse:

    # sprawdzenie czy command został już wcześniej wykonany
    if is_command_already_processed(
        db=db,
        command_name=command.command_name,
        idempotency_key=command.idempotency_key,
    ):
        batch = get_batch_by_id_and_operator_id(
            db=db,
            batch_id=command.batch_id,
            operator_id=command.operator_id,
        )

        # zwrócenie aktualnego batcha bez ponownego wykonywania operacji
        return AssignmentBatchResponse.model_validate(batch)

    # pobranie przypisania operatora
    batch = get_batch_by_id_and_operator_id(
        db=db,
        batch_id=command.batch_id,
        operator_id=command.operator_id,
    )

    # sprawdzenie poprawności przejścia statusu
    validate_status_transition(
        current_status=batch.status,
        new_status=AssignmentStatus.COMPLETED,
    )

    # zmiana statusu przypisania na COMPLETED
    batch.status = AssignmentStatus.COMPLETED
    batch = save_assignment_batch(db, batch)

    # zapis wykonanej operacji w processed_commands
    add_processed_command(
        db=db,
        command_name=command.command_name,
        idempotency_key=command.idempotency_key,
        operator_id=command.operator_id,
    )

    # utworzenie notyfikacji EMAIL oraz PUSH
    create_assignment_completed_notifications(
        db=db,
        batch=batch,
        operator_email=command.completed_by,
        notify_email=command.notify_email,
        notify_push=command.notify_push,
    )

    # zwrócenie zaktualizowanego batcha
    return AssignmentBatchResponse.model_validate(batch)
```

Handler `handle_complete_assignment()` staje się więc centralnym miejscem odpowiedzialnym za wykonanie całego procesu systemowego. W przeciwieństwie do prostych operacji CRUD pojedynczy request nie wykonuje już tylko jednej operacji na bazie danych, lecz uruchamia serię kolejnych kroków realizacji zadania. Wraz z rozwojem aplikacji zaczynamy odchodzić od prostych funkcji wykonujących pojedynczy update rekordu na rzecz bardziej uporządkowanych procesów opisanych za pomocą commandów oraz handlerów.

## Integracja z modułem notifications
Po poprawnym wykonaniu operacji `complete` system automatycznie powinien tworzyć powiadomienie EMAIL i PUSH informujące o zakończeniu przypisania. Aby to osiągnąć tworzymy nowy plik odpowiadający za tworzenie powiadomień związanych z procesem przypisania studentów.
```python
# app/group_assignment/service/assignment_notification_service.py

def create_assignment_completed_notifications(
    db: Session,
    batch: AssignmentBatchORM,
    operator_email: str,
    notify_email: bool,
    notify_push: bool,
) -> None:
```
Wewnątrz funkcji budowana jest treść powiadomienia zawierająca informacje o numerze przypisania, liczbie studentów oraz sumie punktów ECTS.
```python
content = (
    f"Przypisanie {batch.assignment_number} zostało zakończone. "
    f"Liczba studentów: {batch.students_count}. "
    f"Suma ECTS: {batch.total_ects}. "
    f"Status: {batch.status}."
)
```
Następnie system tworzy obiekty `NotificationCreate` dla kanału EMAIL oraz PUSH.
```python
email_notification = NotificationCreate(
    content=content,
    channel=NotificationChannel.EMAIL,
    recipient=operator_email,
    scheduled_at=scheduled_at,
    timezone="UTC",
)
push_notification = NotificationCreate(
    content=content,
    channel=NotificationChannel.PUSH,
    recipient="test",
    scheduled_at=scheduled_at,
    timezone="UTC",
)
```
Obie notyfikacje przekazywane są następnie do wcześniej zaimplementowanego modułu `notifications`:
```python
create_notification(
    db=db,
    notification_data=email_notification,
)
```
Warto zwrócić uwagę na sposób ustawiania czasu wykonania notyfikacji:
```python
scheduled_at = datetime.now(timezone.utc) + timedelta(seconds=1)
```
W poprzednich laboratoriach wszystkie notyfikacje były przetwarzane na czas UTC. Wykorzystanie datetime.now(timezone.utc) pozwala uniknąć problemów związanych ze strefami czasowymi oraz porównywaniem czasu lokalnego z czasem UTC podczas działania workera. Po utworzeniu rekordów w bazie danych dalsze przetwarzanie odbywa się już automatycznie przez wcześniej zaimplementowany worker powiadomień. 



## Zadanie do wykonania na laboratorium

W ramach laboratorium należy uruchomić projekt, sprawdzić działanie aplikacji po wprowadzonych zmianach, a następnie zweryfikować poprawność działania testów.

Wykonaj poniższe kroki:

1. Aktywuj środowisko wirtualne 

    `.venv\Scripts\activate`

2. Uruchom kontenery projektu za pomocą polecenia:<br>
    `docker compose up -d --build`

    Ze względu na zmiany w strukturze bazy danych może być konieczne usunięcie poprzednich wolumenów i ponowne zbudowanie środowiska. W takim przypadku wykonaj:<br>
    `docker compose down -v`

    a następnie ponownie:<br>
    `docker compose up -d --build`

3. Uruchom aplikację poleceniem:<br>
    `uvicorn main:app --reload`

4. Sprawdź działanie usług:
    ntfy: http://localhost:8088/test
    MailHog: http://localhost:8025/

5. Zarejestruj oraz zaloguj operatora przez identity-docs.
    http://127.0.0.1:8000/identity-docs/

6. Utwórz roboczą grupę studentów:
    * pobierz draft,
    * dodaj studentów,
    * sprawdź sumę ECTS oraz liczbę studentów.

7. Zatwierdź przypisanie endpointem `POST /assignments/confirm`

8. Wykonaj operację `POST /assignments/{batch_id}/complete`
    Dodaj nagłówek Idempotency-Key: complete-test-001
    Zweryfikuj:
    * zmianę statusu na COMPLETED,
    * zapis processed_command,
    * utworzenie notyfikacji EMAIL oraz PUSH

9. Sprawdź działanie State Machine - wykonaj complete z innym Idempotency-Key, system powinien zablokować operację.

10. Sprawdź działanie idempotencji - wykonaj complete z tym samym Idempotency-Key, system nie powinien wykonać operacji drugi raz.

## Projekt 3. Etap 2. 
1. Rozszerzenie procesu zamówienia o mechanizmy State Machine, rozwinięty Command Pattern, lekkie CQRS oraz idempotencję. Należy dodać statusy zamówienia PENDING, COMPLETED, CANCELLED wraz z walidacją dozwolonych przejść między nimi. Operacje odczytowe powinny zostać wydzielone do query service, natomiast operacje zmieniające stan systemu powinny wykorzystywać commandy i handlery. Operacja zakończenia zamówienia powinna przyjmować Idempotency-Key, sprawdzać czy command nie został już wykonany, zmieniać status zamówienia na COMPLETED, zapisywać wykonany command w processed_commands oraz blokować ponowne wykonanie tej samej operacji.
   
2. Integracja zakończenia zamówienia z modułem notifications. Po poprawnym zakończeniu zamówienia system powinien utworzyć powiadomienie EMAIL oraz PUSH informujące użytkownika o zakończeniu realizacji zamówienia. Ponowne wykonanie requestu z tym samym Idempotency-Key nie powinno tworzyć kolejnych powiadomień. Powiadomienia powinny zostać przetworzone przez wcześniej zaimplementowany worker.
   
3. Przygotowanie testów integracyjnych w pliku test_basket.py. Testy powinny obejmować pełny proces użytkownika: 
* rejestrację/logowanie
* dodanie produktów do koszyka
* checkout
* utworzenie zamówienia
* zakończenie zamówienia
* zmianę statusu na COMPLETED
* sprawdzenie działania Idempotency-Key
* blokadę ponownego wykonania operacji z innym kluczem dla zakończonego zamówienia
* weryfikację, że po zakończeniu zamówienia powstają powiadomienia EMAIL i PUSH.
