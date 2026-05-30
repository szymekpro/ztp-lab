# Sprawozdanie - Projekt 3

**Przedmiot:** Zaawansowane Techniki Programowania
**Projekt:** Projekt 3 (Etapy 1-3, na podstawie Lab 7, 8, 9)
**Imię i Nazwisko:** _[uzupełnić]_
**Grupa:** _[uzupełnić]_

---

## 1. Wstęp

### a. Opis dodanych do struktury projektu modułów - moduł `identity` oraz `cart`

W ramach Projektu 3 do istniejącej aplikacji backendowej dodane zostały dwa nowe moduły, które rozszerzają system o obsługę użytkowników oraz proces zakupowy:

**Moduł `identity`** (Etap 1, Laboratorium 7) - odpowiada za uwierzytelnianie operatora systemu oraz utrzymywanie jego sesji. Moduł utrzymuje strukturę warstwową stosowaną w pozostałych modułach projektu:

- `app/identity/model/` - modele ORM (`OperatorORM`, `OperatorSessionORM`) oraz schematy Pydantic (`auth_schema.py`),
- `app/identity/data/` - repozytoria (`operator_repository.py`, `operator_session_repository.py`),
- `app/identity/service/` - logika biznesowa (`auth_service.py`, `password_hasher.py`, `auth_validators.py`, `auth_exceptions.py`),
- `app/identity/web/` - endpointy HTTP (`routes.py`).

Moduł posiada również własną podstronę z dokumentacją Swagger pod adresem `/identity-docs/` (`docs_app.py`).

**Moduł `cart`** (Etap 2 i 3, Laboratorium 8 i 9) - odpowiada za obsługę koszyka produktów (`cart_drafts`, `cart_draft_items`), proces checkout, utworzenie i zakończenie zamówienia oraz przechowanie historii zamówień (`orders`, `order_items`). Moduł posiada również tabelę `processed_commands` używaną do realizacji idempotencji. Struktura modułu:

- `app/cart/model/` - modele ORM (`CartDraftORM`, `CartDraftItemORM`, `OrderORM`, `OrderItemORM`, `ProcessedCommandORM`), schematy Pydantic (`cart_schema.py`) oraz stałe statusów (`order_status.py`),
- `app/cart/data/` - repozytorium (`cart_repository.py`) obsługujące wszystkie operacje bazodanowe modułu,
- `app/cart/service/` - logika biznesowa: serwis koszyka (`cart_service.py`), commandy (`checkout_command.py`, `complete_order_command.py`), handlery (`checkout_handler.py`, `complete_order_handler.py`), query service (`order_query_service.py`), state machine (`order_state_machine.py`), serwis powiadomień (`order_notification_service.py`),
- `app/cart/web/` - endpointy (`routes.py`) - routery `cart_router` (prefix `/cart`) oraz `orders_router` (prefix `/orders`).

Moduł posiada również własną dokumentację Swagger pod adresem `/cart-docs/` (`docs_app.py`).

### b. Opis głównych założeń projektu oraz zależności między modułami `identity`, `cart`, `notifications`

Główne założenie projektu opiera się na rozszerzeniu aplikacji o pełen przebieg procesu zakupowego rozpoczynającego się od rejestracji i uwierzytelnienia użytkownika, przez zarządzanie koszykiem, złożenie i zakończenie zamówienia, aż do automatycznego wysłania powiadomień o zakończeniu realizacji zamówienia. Każdy moduł realizuje wąsko określony zakres odpowiedzialności, co odpowiada zasadzie Single Responsibility Principle.

Zależności pomiędzy modułami:

- **`identity` → `cart`** - moduł koszyka identyfikuje aktualnie zalogowanego operatora wyłącznie na podstawie ciasteczka `auth_token`. W każdym endpointcie modułu `cart` używana jest zależność `get_current_operator_dependency`, która wykorzystuje funkcję `get_current_operator` z modułu `identity`. Klucz `operator_id` jest następnie używany jako klucz obcy w tabelach `cart_drafts`, `orders` oraz `processed_commands`. Bez aktywnej sesji moduł `cart` zwraca błąd 401.
- **`cart` → `notifications`** - po zakończeniu zamówienia handler `handle_complete_order` wywołuje `create_order_completed_notifications` z `order_notification_service.py`, który tworzy obiekty `NotificationCreate` i przekazuje je do `create_notification` z modułu `notifications`. Dalsze przetwarzanie powiadomień (EMAIL/PUSH) odbywa się automatycznie przez wcześniej zaimplementowany worker (`notification_worker`).
- **`cart` → `REST` (products)** - moduł koszyka odwołuje się do repozytorium produktów (`get_product_by_id`, `save_product`) w celu sprawdzenia dostępności produktu i pomniejszenia stanu magazynowego po checkout.

Schemat zależności:

```
identity (operator + sesja)
    │
    └──► cart (koszyk + zamówienia + idempotencja)
            │
            ├──► REST/products (stan magazynowy)
            └──► notifications (EMAIL + PUSH)
```

---

## 2. Model użytkownika i sesji

### a. Opis hashowania hasła i zastosowanego algorytmu

Hasła operatorów nigdy nie są przechowywane w bazie w postaci jawnej. W bazie zapisany jest jedynie skrót hasła wraz z losowym saltem. Wykorzystany został algorytm **PBKDF2 (Password-Based Key Derivation Function 2)** z funkcją skrótu **SHA-256**.

Wybór PBKDF2 wynika z faktu, że jest on dostępny w standardowej bibliotece Pythona (`hashlib`) - nie wymaga instalacji dodatkowych pakietów - i jest powszechnie stosowany w systemach produkcyjnych. Jest to KDF (Key Derivation Function), które celowo zwiększa koszt obliczenia pojedynczego hasha, co utrudnia ataki brute-force i ataki typu rainbow table.

Implementacja znajduje się w `app/identity/service/password_hasher.py`:

```python
PBKDF2_ITERATIONS = 100_000
SALT_BYTES = 16


def hash_password(password: str) -> str:
    salt = secrets.token_hex(SALT_BYTES)
    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    )
    return f"{salt}${derived_key.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt, expected_hash = stored_hash.split("$", 1)
    except ValueError:
        return False

    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    ).hex()

    return hmac.compare_digest(derived_key, expected_hash)
```

Kluczowe elementy implementacji:

- **Salt** - dla każdego użytkownika generowany jest losowy 16-bajtowy salt (`secrets.token_hex`). Salt powoduje, że dwóch użytkowników o identycznych hasłach będzie miało różne wartości hasha. Dodatkowo unieważnia gotowe rainbow tables.
- **100 000 iteracji** - PBKDF2 wykonuje wewnętrznie taką liczbę powtórzeń funkcji skrótu. Zwiększa to koszt obliczeń, co spowalnia ewentualny atak brute-force.
- **Format zapisu** `salt$hash` - zarówno salt, jak i hash są przechowywane razem w jednym polu `password_hash`, co upraszcza weryfikację.
- **`hmac.compare_digest`** - porównanie hasha odbywa się w sposób odporny na ataki czasowe (timing attacks).

Walidacja hasła (`auth_validators.py`) wymaga przed zahashowaniem: minimum 8 znaków, wielkiej litery, cyfry oraz znaku specjalnego.

### b. Opis obsługi ciasteczka wraz ze zrzutami ekranu (Swagger)

Po pomyślnym logowaniu (`POST /auth/login`) backend ustawia ciasteczko HTTP o nazwie `auth_token`, którego wartością jest token sesji (32-bajtowy ciąg URL-safe wygenerowany przez `secrets.token_urlsafe(32)`). Przeglądarka automatycznie dołącza to ciasteczko do każdego kolejnego żądania, dzięki czemu backend może zidentyfikować zalogowanego operatora bez konieczności logowania na każde żądanie.

Fragment kodu odpowiedzialny za ustawienie ciasteczka (`app/identity/web/routes.py`):

```python
response.set_cookie(
    key="auth_token",
    value=session_token,
    httponly=True,
    samesite="lax",
    secure=False,
    max_age=SESSION_MAX_AGE_SECONDS,
)
```

Znaczenie parametrów:

| Parametr | Wartość | Opis |
|----------|---------|------|
| `key` | `auth_token` | Nazwa ciasteczka. |
| `value` | token sesji | Losowy identyfikator sesji zapisany również w bazie. |
| `httponly` | `True` | Ciasteczko niedostępne z poziomu JavaScript - chroni przed atakami XSS. |
| `samesite` | `"lax"` | Ogranicza wysyłanie ciasteczka między domenami. |
| `secure` | `False` | Cookie działa po HTTP (w środowisku deweloperskim). W produkcji powinno być `True`. |
| `max_age` | `SESSION_MAX_AGE_SECONDS` | Czas życia ciasteczka po stronie klienta. |

**Zrzuty ekranu Swagger:**

> _Tutaj należy wstawić zrzuty ekranu z `http://127.0.0.1:8000/identity-docs/` przedstawiające:_
>
> - _wykonanie `POST /auth/register` z body JSON i odpowiedzią 201,_
> - _wykonanie `POST /auth/login` i zakładkę Headers/Cookies pokazującą `Set-Cookie: auth_token=...`,_
> - _wykonanie `GET /auth/me` z aktywnym ciasteczkiem - odpowiedź 200 z danymi operatora,_
> - _wykonanie `POST /auth/logout` - odpowiedź 204 i usunięcie ciasteczka._

### c. Mechanizmy odpowiadające za nadpisywanie sesji, wygasanie sesji po określonym czasie i jej przedłużenie

W projekcie zastosowano model sesji przechowywanej po stronie serwera (tabela `operator_sessions`) z identyfikatorem przekazywanym jako ciasteczko HTTP po stronie klienta. Maksymalny czas życia sesji konfigurowany jest stałą:

```python
SESSION_MAX_AGE_SECONDS = 900
```

#### Nadpisywanie sesji

Każde wywołanie `POST /auth/login` przy aktywnym `auth_token` skutkuje wcześniejszym wylogowaniem poprzedniej sesji. Dzięki temu w danym momencie w przeglądarce może istnieć tylko jedna aktywna sesja, a baza nie gromadzi nieużywanych rekordów. Fragment z `routes.py`:

```python
if auth_token is not None:
    logout_operator(db, auth_token)

operator, session_token = login_operator(...)
```

Funkcja `logout_operator` usuwa rekord sesji z bazy (`delete_session_by_token`), a nowy `login_operator` zakłada nowy rekord z nowym tokenem.

#### Wygasanie sesji po określonym czasie

Walidacja czasu sesji odbywa się przy każdym wywołaniu chronionego endpointu w funkcji `get_current_operator` (`auth_service.py`):

```python
def is_session_expired(last_used_at: datetime) -> bool:
    return datetime.now() - last_used_at > timedelta(seconds=SESSION_MAX_AGE_SECONDS)


def get_current_operator(db: Session, session_token: str) -> OperatorORM:
    session = get_session_by_token(db, session_token)
    if session is None:
        raise AuthorizationError("Brak aktywnej sesji.")

    if is_session_expired(session.last_used_at):
        delete_session_by_id(db, session.id)
        raise AuthorizationError("Sesja wygasła.")
    ...
```

Jeżeli od czasu ostatniego użycia (`last_used_at`) upłynęło więcej niż `SESSION_MAX_AGE_SECONDS`, sesja jest aktywnie usuwana z bazy, a klient otrzymuje odpowiedź 401.

#### Przedłużanie sesji (sliding session)

Sesja nie wygasa po stałym czasie od logowania, lecz po określonym czasie braku aktywności użytkownika. Mechanizm jest dwustronny:

- **Po stronie serwera** - przy każdym poprawnym wywołaniu `get_current_operator` aktualizowane jest pole `last_used_at` (`update_session_last_used`).
- **Po stronie klienta** - endpoint `GET /auth/me` ponownie ustawia ciasteczko `auth_token` z odświeżonym `max_age`, dzięki czemu cookie po stronie przeglądarki również jest przedłużane.

Dzięki temu aktywny użytkownik (np. korzystający z aplikacji co kilka minut) nie zostanie wylogowany, a nieaktywny zostanie wylogowany automatycznie po 15 minutach.

---

## 3. Koszyk produktów

### a. Opis mechanizmu zatwierdzenia koszyka

Operacja checkout (`POST /cart/checkout`) realizowana jest w `app/cart/service/checkout_handler.py` w funkcji `handle_checkout`. W przeciwieństwie do prostych operacji CRUD jest to proces biznesowy złożony z kilku powiązanych kroków:

1. pobranie i walidacja koszyka,
2. ponowne sprawdzenie stanu magazynowego dla każdej pozycji,
3. agregacja danych (liczba pozycji, suma cen),
4. utworzenie rekordu zamówienia,
5. wygenerowanie numeru zamówienia w formacie `ZAM-YYYYMMDD-000001`,
6. zapis snapshotów produktów w pozycjach zamówienia,
7. pomniejszenie stanu magazynowego,
8. wyczyszczenie koszyka roboczego.

#### i. Agregacja danych

System na bieżąco wylicza liczbę pozycji oraz sumaryczną cenę zamówienia na podstawie danych z koszyka. Wartości te nie są przechowywane redundantnie w koszyku, lecz wyliczane przed zapisem zamówienia:

```python
def _calculate_items_count(cart: CartDraftORM) -> int:
    return len(cart.items)


def _calculate_total_price(cart: CartDraftORM) -> float:
    return sum(float(item.product.price) * item.quantity for item in cart.items)
```

Dzięki temu dane są zawsze spójne z aktualnym stanem koszyka.

#### ii. Utworzenie rekordu zamówienia

Po agregacji tworzony jest rekord w tabeli `orders` z tymczasowym numerem `"TEMP"`, statusem `PENDING` oraz zagregowanymi wartościami:

```python
def _create_order(db, operator_id, items_count, total_price) -> OrderORM:
    order = OrderORM(
        operator_id=operator_id,
        order_number="TEMP",
        status="PENDING",
        items_count=items_count,
        total_price=total_price,
    )
    order = add_order(db, order)
    order.order_number = _generate_order_number(order.id)
    db.add(order)
    db.commit()
    db.refresh(order)
    return order
```

Następnie tworzone są pozycje zamówienia `OrderItemORM` zawierające snapshot danych produktu (`product_name`, `product_price`, `quantity`) - dzięki temu późniejsza zmiana ceny lub nazwy produktu nie wpłynie na historię zamówienia.

#### iii. Generowanie numeru zamówienia

Numer zamówienia generowany jest po zapisaniu rekordu i uzyskaniu jego `id`:

```python
def _generate_order_number(order_id: int) -> str:
    today = datetime.now().strftime("%Y%m%d")
    return f"ZAM-{today}-{order_id:06d}"
```

Format: `ZAM-YYYYMMDD-000001`. Dzięki użyciu `id` rekordu (z `UNIQUE` na kolumnie `order_number`) numer jest globalnie unikalny.

#### iv. Czyszczenie grupy roboczej (koszyka)

Po wszystkich operacjach koszyk operatora jest czyszczony - usuwane są wszystkie rekordy `cart_draft_items` powiązane z `cart_id` aktualnego operatora:

```python
def clear_cart_items(db, cart_id):
    query = delete(CartDraftItemORM).where(CartDraftItemORM.cart_id == cart_id)
    db.execute(query)
    db.commit()
```

Pomniejszenie stanu magazynowego odbywa się w `_create_order_items`:

```python
product.quantity -= item.quantity
save_product(db, product)
```

### b. Opis zastosowanego wzorca projektowego - Command Pattern

**Krótki opis:** Command Pattern to wzorzec projektowy, w którym żądanie wykonania operacji jest opakowywane w obiekt zawierający wszystkie potrzebne dane. Obiekt ten (command) jest następnie przekazywany do handlera, który realizuje całą logikę biznesową. Wzorzec oddziela "co należy zrobić" (command) od "jak to zrobić" (handler).

**Zastosowanie:** Wzorzec jest szczególnie użyteczny wtedy, gdy operacja przestaje być prostym CRUD i staje się procesem biznesowym składającym się z wielu kroków. Pozwala uporządkować kod, ułatwia testowanie (można testować handler niezależnie od warstwy HTTP) oraz upraszcza dodawanie nowych parametrów - zamiast rozszerzać listę argumentów funkcji, dodajemy pole do klasy command.

**Implementacja w projekcie:**

W projekcie wykorzystywana jest uproszczona wersja Command Pattern. Mamy dwa commandy:

1. **`CheckoutCommand`** (`checkout_command.py`) - prosty command przekazujący jedynie `operator_id`:

```python
class CheckoutCommand:
    def __init__(self, operator_id: int):
        self.operator_id = operator_id
```

Wywoływany w endpointcie:

```python
command = CheckoutCommand(operator_id=operator.id)
return handle_checkout(db=db, command=command)
```

2. **`CompleteOrderCommand`** (`complete_order_command.py`) - rozbudowany command zawierający wszystkie dane niezbędne do zakończenia zamówienia, włącznie z kluczem idempotencji i ustawieniami powiadomień:

```python
class CompleteOrderCommand:
    command_name = "CompleteOrderCommand"

    def __init__(
        self,
        operator_id: int,
        order_id: int,
        idempotency_key: str,
        completed_by: str,
        source: str = "API",
        notify_email: bool = True,
        notify_push: bool = True,
        note: str | None = None,
    ):
        ...
```

Atrybut klasy `command_name` jest wykorzystywany do identyfikacji typu operacji w tabeli `processed_commands` na potrzeby idempotencji.

Endpoint `POST /orders/{order_id}/complete` jedynie buduje command i przekazuje go do handlera:

```python
command = CompleteOrderCommand(
    operator_id=operator.id,
    order_id=order_id,
    idempotency_key=idempotency_key,
    completed_by=operator.email,
    source="API",
    notify_email=True,
    notify_push=True,
    note="Zamówienie zakończone przez operatora.",
)
return handle_complete_order(db=db, command=command)
```

Dzięki temu endpoint pozostaje cienką warstwą HTTP, a cała logika biznesowa (walidacja idempotencji, walidacja przejścia statusu, zapis processed_command, utworzenie powiadomień) znajduje się w handlerze. W projekcie nie został zaimplementowany pełny Command Bus - ze względu na małą liczbę commandów handlery wywoływane są bezpośrednio.

### c. CQRS - krótki opis, zastosowanie oraz implementacja w projekcie

**Krótki opis:** CQRS (Command Query Responsibility Segregation) to wzorzec architektoniczny polegający na rozdzieleniu operacji zmieniających stan systemu (Command) od operacji odczytujących dane (Query). Każda z tych grup operacji może mieć inne wymagania (Command - walidacja, transakcje, side-effects; Query - wydajne odczyty, formatowanie pod frontend), dlatego ich rozdzielenie zwiększa czytelność i ułatwia rozwój aplikacji.

**Zastosowanie:** CQRS znajduje zastosowanie w aplikacjach, w których operacje odczytowe i zapisujące zaczynają znacząco się różnić. W projekcie zastosowano uproszczoną wersję CQRS - bez osobnych modeli odczytu/zapisu czy event sourcing - skupiając się jedynie na rozdzieleniu odpowiedzialności w warstwie service.

**Implementacja w projekcie:**

Wzorzec endpointów:

- `POST` → command → handler → zmiana stanu (`handle_checkout`, `handle_complete_order`)
- `GET` → query service → odczyt danych (`list_orders`, `get_order_details`)

Operacje odczytowe zostały wydzielone do pliku `app/cart/service/order_query_service.py`, który zawiera wyłącznie funkcje pobierające dane:

```python
def list_orders(db: Session, operator_id: int) -> list[OrderListItemResponse]:
    orders = get_orders_by_operator_id(db=db, operator_id=operator_id)
    return [OrderListItemResponse.model_validate(order) for order in orders]


def get_order_details(db: Session, operator_id: int, order_id: int) -> OrderResponse:
    order = get_order_by_id_and_operator_id(db=db, order_id=order_id, operator_id=operator_id)
    if order is None:
        raise CartNotFoundError("Zamówienie nie istnieje.")
    return OrderResponse.model_validate(order)
```

Operacje zmieniające stan znajdują się w handlerach (`checkout_handler.py`, `complete_order_handler.py`), które są wywoływane wyłącznie z endpointów POST. Dzięki temu projekt jest uporządkowany - czytając plik `order_query_service.py` mamy pewność, że żadna funkcja nie wprowadzi zmian w systemie.

#### Tworzenie powiadomień

W ramach handlera `handle_complete_order` po zmianie statusu zamówienia na `COMPLETED` automatycznie tworzone są powiadomienia EMAIL oraz PUSH przez funkcję `create_order_completed_notifications` (`order_notification_service.py`):

```python
def create_order_completed_notifications(db, order, operator_email, notify_email, notify_push):
    content = (
        f"Zamówienie {order.order_number} zostało zakończone. "
        f"Liczba pozycji: {order.items_count}. "
        f"Suma: {order.total_price} PLN. "
        f"Status: {order.status}."
    )

    scheduled_at = datetime.now(timezone.utc) + timedelta(seconds=1)

    if notify_email:
        create_notification(db, NotificationCreate(
            content=content,
            channel=NotificationChannel.EMAIL,
            recipient=operator_email,
            scheduled_at=scheduled_at,
            timezone="UTC",
        ))

    if notify_push:
        create_notification(db, NotificationCreate(
            content=content,
            channel=NotificationChannel.PUSH,
            recipient="test",
            scheduled_at=scheduled_at,
            timezone="UTC",
        ))
```

Treść powiadomienia zawiera numer zamówienia, liczbę pozycji, sumaryczną kwotę oraz status. Czas wysyłki ustawiony jest jako `datetime.now(timezone.utc) + 1s`, aby zsynchronizować się z workerem powiadomień działającym w UTC. Dalsze przetwarzanie odbywa się automatycznie przez `notification_worker` zaimplementowany w poprzednich laboratoriach.

#### Idempotencja

Idempotencja jest realizowana na poziomie commandu i opiera się na tabeli `processed_commands`:

```sql
CREATE TABLE IF NOT EXISTS processed_commands (
    id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    command_name VARCHAR NOT NULL,
    idempotency_key VARCHAR NOT NULL,
    operator_id INTEGER NOT NULL REFERENCES operators(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_processed_command_key UNIQUE (command_name, idempotency_key)
);
```

Mechanizm w handlerze `handle_complete_order` (`complete_order_handler.py`):

```python
def handle_complete_order(db, command: CompleteOrderCommand) -> OrderResponse:
    if is_command_already_processed(
        db=db,
        command_name=command.command_name,
        idempotency_key=command.idempotency_key,
    ):
        order = get_order_by_id_and_operator_id(...)
        return OrderResponse.model_validate(order)

    order = get_order_by_id_and_operator_id(...)
    validate_status_transition(
        current_status=order.status,
        new_status=OrderStatus.COMPLETED,
    )

    order.status = OrderStatus.COMPLETED
    order = save_order(db, order)

    add_processed_command(
        db=db,
        command_name=command.command_name,
        idempotency_key=command.idempotency_key,
        operator_id=command.operator_id,
    )

    create_order_completed_notifications(...)

    return OrderResponse.model_validate(order)
```

Działanie:

- **Ten sam `Idempotency-Key`** - jeśli w bazie istnieje rekord (`command_name`, `idempotency_key`), handler zwraca aktualny stan zamówienia bez ponownej zmiany statusu i bez ponownego utworzenia powiadomień. Operacja jest bezpieczna do ponownego wywołania (np. przy retry sieciowym).
- **Inny `Idempotency-Key` dla zamówienia o statusie `COMPLETED`** - handler dochodzi do `validate_status_transition`, które rzuca `CartValidationError` z `order_state_machine.py`, ponieważ ze stanu `COMPLETED` nie istnieje żadne dozwolone przejście. Endpoint zwraca błąd 400. Dzięki temu po zakończeniu zamówienia kolejne próby jego zakończenia są blokowane niezależnie od użytego klucza idempotencji.

Stałe i dozwolone przejścia statusu (`order_state_machine.py`):

```python
ALLOWED_STATUS_TRANSITIONS = {
    OrderStatus.PENDING: {OrderStatus.COMPLETED, OrderStatus.CANCELLED},
    OrderStatus.COMPLETED: set(),
    OrderStatus.CANCELLED: set(),
}
```

---

## 4. Testy integracyjne

Testy integracyjne zostały umieszczone w pliku `tests/test_basket.py`. Wykorzystują `TestClient` z FastAPI oraz fixture `client` z `tests/conftest.py`, który nadpisuje zależność `get_db` na sesję transakcyjną - dzięki temu każdy test działa w osobnej transakcji rollbackowanej po zakończeniu, a baza nie gromadzi danych testowych.

Pomocnicze funkcje:

- `_unique_email()` - generuje unikalny email,
- `_register_and_login(client, email)` - rejestruje i loguje operatora,
- `_add_product_and_checkout(client)` - dodaje produkt do koszyka i wykonuje checkout,
- `_setup(client)` - łączy oba kroki w jedno przygotowanie testu.

### a. Rejestracja / logowanie - `test_register_and_login`

Test wykonuje pełny scenariusz uwierzytelnienia:

1. `POST /api/v1/auth/register` - rejestracja nowego operatora z poprawnym hasłem,
2. weryfikacja, że odpowiedź ma status 201 oraz pole `email`, `is_active=True`,
3. `POST /api/v1/auth/login` - logowanie zarejestrowanym operatorem,
4. weryfikacja, że odpowiedź ma status 200 i zawiera ciasteczko `auth_token`.

### b. Dodanie produktów do koszyka - `test_add_products_to_cart`

Test sprawdza:

1. dodanie produktu `product_id=1` z `quantity=2` przez `POST /api/v1/cart/items`,
2. status odpowiedzi 201,
3. `items_count == 1`, poprawne `product.id`, `quantity` oraz `total_price > 0`.

### c. Checkout - `test_checkout_creates_order_with_pending_status`

Test sprawdza:

1. dodanie produktu do koszyka,
2. wywołanie `POST /api/v1/cart/checkout`,
3. status odpowiedzi 201,
4. status zamówienia `PENDING`, `items_count == 1`,
5. numer zamówienia rozpoczyna się od `ZAM-`.

### d. Utworzenie zamówienia

Każdy z testów (`test_checkout_creates_order_with_pending_status`, `test_complete_order_*`) weryfikuje utworzenie zamówienia po checkout - rekord otrzymuje numerację `ZAM-YYYYMMDD-000001`, status `PENDING`, agregowaną liczbę pozycji oraz `id`.

### e. Zakończenie zamówienia oraz f. Zmiana statusu na `COMPLETED` - `test_complete_order_changes_status_to_completed`

Test sprawdza:

1. przygotowanie zamówienia (`_setup`),
2. wywołanie `POST /api/v1/orders/{order_id}/complete` z nagłówkiem `Idempotency-Key`,
3. status odpowiedzi 200,
4. odpowiedź zawiera `id` zamówienia,
5. **status zamówienia został zmieniony na `COMPLETED`**.

### g. Sprawdzenie działania `Idempotency-Key` - `test_idempotency_key_same_key_returns_200_without_reprocessing`

Test sprawdza:

1. wywołanie `complete` z `Idempotency-Key=X` → status 200, status `COMPLETED`,
2. ponowne wywołanie `complete` z tym samym `Idempotency-Key=X` → status 200, status nadal `COMPLETED`, ten sam `id`,
3. handler nie wykonuje ponownie operacji - krótkie wejście (`is_command_already_processed`) zwraca aktualny stan zamówienia.

### h. Blokada ponownego wykonania operacji z innym kluczem dla zakończonego zamówienia - `test_different_idempotency_key_on_completed_order_is_blocked`

Test sprawdza:

1. wywołanie `complete` z `Idempotency-Key=K1` → status 200, status `COMPLETED`,
2. wywołanie `complete` z innym `Idempotency-Key=K2` dla zakończonego zamówienia,
3. **status odpowiedzi 400**, w treści błędu pojawia się słowo `COMPLETED` (z `order_state_machine`).

Test dowodzi, że nie wystarczy zmienić `Idempotency-Key`, aby ponownie zakończyć zamówienie - State Machine blokuje wszystkie przejścia z `COMPLETED`.

### i. Powiadomienia EMAIL i PUSH

Test `test_complete_order_creates_email_and_push_notifications` sprawdza:

1. zakończenie zamówienia,
2. pobranie listy powiadomień z `GET /api/v1/notifications`,
3. filtrowanie po `order_number` w treści,
4. w zbiorze kanałów dla tych powiadomień znajduje się zarówno `EMAIL`, jak i `PUSH`.

Dodatkowo test `test_idempotency_key_does_not_create_duplicate_notifications` sprawdza:

1. wykonanie `complete` z `Idempotency-Key=X` → utworzenie powiadomień,
2. pobranie liczby powiadomień dla `order_number`,
3. ponowne wywołanie `complete` z `Idempotency-Key=X`,
4. ponowne pobranie liczby powiadomień - liczba nie zmienia się.

Dzięki temu mamy pewność, że idempotencja nie tworzy duplikatów powiadomień.

### Zrzuty ekranu wykonanych testów oraz powstałych powiadomień

> _Tutaj należy wstawić zrzuty ekranu przedstawiające:_
>
> - _wynik wywołania `pytest tests/test_basket.py -v` - lista testów, status PASSED dla każdego,_
> - _zrzut z `http://localhost:8025/` (MailHog) z powiadomieniami EMAIL informującymi o zakończeniu zamówienia,_
> - _zrzut z `http://localhost:8088/test` (ntfy) z powiadomieniami PUSH,_
> - _zrzut wyniku `GET /api/v1/notifications` ze Swaggera pokazujący dwa wpisy (EMAIL + PUSH) dla danego `order_number`._

---

## Podsumowanie

W ramach Projektu 3 aplikacja została rozszerzona o pełen proces zakupowy realizowany przez dwa nowe moduły. Moduł `identity` wprowadził bezpieczne uwierzytelnianie operatora oparte na ciasteczkach i sesjach po stronie serwera, z hashowaniem haseł algorytmem PBKDF2 oraz mechanizmem sliding session. Moduł `cart` wprowadził koszyk produktów, proces checkout oraz cykl życia zamówienia obejmujący statusy `PENDING`, `COMPLETED`, `CANCELLED`. Dodatkowo wprowadzono uproszczone CQRS, rozwinięty Command Pattern oraz idempotencję na poziomie commandów, dzięki czemu kluczowa operacja zakończenia zamówienia jest bezpieczna do retry oraz blokuje powtórne wykonanie po osiągnięciu stanu końcowego. Pełna sekwencja procesu jest pokryta testami integracyjnymi w `tests/test_basket.py`.
