# Laboratorium 10
Celem Laboratorium 10 jest rozpoczęcie implementacji warstwy frontendowej aplikacji z wykorzystaniem biblioteki React oraz integracja istniejącego backendu FastAPI z rzeczywistym interfejsem użytkownika.

Do tej pory aplikacja była testowana głównie przy użyciu Swagger/OpenAPI oraz bezpośrednich requestów HTTP. Backend pełnił rolę samodzielnego systemu API. W tym laboratorium projekt zostaje rozszerzony o frontend typu SPA (Single Page Application), który komunikuje się z backendem wyłącznie poprzez endpointy REST API.

Laboratorium skupia się przede wszystkim na pokazaniu sposobu współpracy Reacta z backendem FastAPI. Celem nie jest tworzenie rozbudowanego interfejsu graficznego, lecz zbudowanie działającej aplikacji frontendowej wykorzystującej istniejące endpointy backendowe.

## React i architektura SPA
React jest biblioteką frontendową, która służy do budowania interfejsów użytkownika opartych o komponenty. W przeciwieństwie do klasycznych aplikacji renderujących HTML po stronie backendu, React działa po stronie przeglądarki i samodzielnie zarządza widokami aplikacji.

Takie podejście określane jest jako SPA (Single Page Application). W aplikacjach SPA frontend odpowiada za:
* renderowanie widoków,
* routing,
* obsługę formularzy,
* komunikację z backendem,
* zarządzanie stanem interfejsu użytkownika.
Backend przestaje odpowiadać za generowanie HTML i pełni wyłącznie rolę API zwracającego dane w formacie JSON.

W naszym projekcie React komunikuje się z backendem FastAPI poprzez endpointy REST API przygotowane we wcześniejszych laboratoriach. Dzięki temu frontend staje się niezależną warstwą aplikacji wykorzystującą istniejącą logikę backendową.

## Utworzenie projektu React
Przed rozpoczęciem pracy z React konieczna jest instalacja środowiska Node.js wraz z menedżerem pakietów `npm`. 

Node.js można pobrać z oficjalnej strony [link](https://nodejs.org/en)

Po instalacji warto zweryfikować poprawność konfiguracji poleceniami:
```
node -v
npm -v
```
W projekcie frontend zostanie umieszczony w osobnym folderze **frontend**, znajdującym się obok backendu FastAPI.W przeciwieństwie do wcześniejszych modułów backendowych frontend React nie zostaje umieszczony wewnątrz folderu **app/**. Wynika to z faktu, że frontend stanowi całkowicie osobną aplikację posiadającą własne zależności, własny proces uruchomieniowy oraz osobne środowisko deweloperskie.

Do utworzenia projektu React wykorzystujemy narzędzie `create-react-app`, które automatycznie generuje podstawową strukturę aplikacji frontendowej wraz z konfiguracją Reacta.
W głównym katalogu projektu wykonujemy polecenie:
```
npx create-react-app frontend
```
Polecenie automatycznie utworzy folder **frontend**, pobierze wymagane zależności, skonfiguruje React i przygotuje podstawową strukturę projektu frontendowego.
Struktura projektu po utworzeniu Reacta będzie wyglądała następująco:
```
project/
├── app/
├── tests/
├── frontend/
├── main.py
├── requirements.txt
└── docker-compose.yml
```
Po zakończeniu instalacji i utworzeniu folderu, przechodzimy w terminalu do folderu **frontend** `cd frontend`, a następnie uruchamiamy poleceniem `npm start`. React automatycznie uruchomi lokalny serwer dostępny pod adresem `http://localhost:3000`. Frontend będzie działał w naszym projekcie jako osobna aplikacja uruchomiona na oddzielnym porcie. 

## Komunikacja frontend - backend
Frontend React oraz backend FastAPI działają jako dwie osobne aplikacje uruchomione na różnych portach.
W naszym przypadku:
* frontend: http://localhost:3000
* backend:  http://localhost:8000

Dla przeglądarki są to dwa różne adresy źródłowe. Z tego powodu backend musi jawnie zezwolić frontendowi na wykonywanie requestów HTTP. Do tego służy mechanizm `CORS (Cross-Origin Resource Sharing)`.CORS jest mechanizmem bezpieczeństwa przeglądarki, który blokuje wykonywanie requestów pomiędzy różnymi adresami źródłowymi bez wyraźnej zgody backendu.

W pliku `main.py` dodajemy middleware:
```python
# main.py

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Parametr `allow_origins` określa, z jakich adresów frontend może komunikować się z backendem. W naszym przypadku dopuszczamy frontend uruchomiony lokalnie na porcie 3000.

Szczególnie ważne jest ustawienie `allow_credentials=True`, ponieważ backend korzysta z sesji opartej o cookie `auth_token`. Jeżeli frontend ma wysyłać requesty jako użytkownik, przeglądarka musi mieć możliwość dołączania cookie do zapytań frontendu kierowanych do backendu.

Po stronie Reacta również trzeba wskazać, że requesty mają zawierać dane uwierzytelniające. Robimy to w pliku `client.js`.

```javascript
// frontend/src/api/client.js

const API_URL = "http://localhost:8000";

export async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,

    // dołączanie cookie auth_token do requestów
    credentials: "include",

    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  // obsługa błędów HTTP
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || "Błąd requestu.");
  }
  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export function apiGet(path) {
  return apiRequest(path, {
    method: "GET",
  });
}

export function apiPost(path, data) {
  return apiRequest(path, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function apiDelete(path) {
  return apiRequest(path, {
    method: "DELETE",
  });
}

```
Fragment `credentials: "include"` powoduje automatyczne dołączanie cookie `auth_token` do requestów wysyłanych z Reacta do backendu FastAPI. Dzięki temu backend może rozpoznawać zalogowanego użytkownika podczas wywoływania kolejnych endpointów.

Na końcu pliku definiujemy uproszczone funkcje dla najczęściej wykorzystywanych metod HTTP:
* apiGet()
* apiPost()
* apiDelete()
Dzięki temu komponenty Reacta mogą wykonywać requesty w dużo prostszy sposób:
```js
await apiGet("/students");

await apiPost("/auth/login", {
  email: email,
  password: password,
});

await apiDelete(`/assignments/draft/items/${itemId}`);
```
## Routing frontendowy
W klasycznych aplikacjach backendowych przejście pomiędzy podstronami zwykle powoduje przeładowanie całego dokumentu HTML po stronie serwera. W aplikacjach `SPA (Single Page Application)` routing obsługiwany jest po stronie Reacta bez przeładowywania całej strony. 

Do obsługi routingu wykorzystujemy bibliotekę `React Router`. W pliku `App.js` definiujemy główne trasy aplikacji:
```js
// frontend/src/App.js
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
```
Cała aplikacja zostaje umieszczona wewnątrz BrowserRouter:
```js
<BrowserRouter>
  <Routes>

  </Routes>
</BrowserRouter>
```
Następnie definiujemy poszczególne widoki aplikacji:
```js
<Route
  path="/login"
  element={<LoginPage />}
/>

<Route
  path="/register"
  element={<RegisterPage />}
/>

<Route
  path="/students"
  element={<StudentsPage />}
/>
```

W aplikacji wykorzystujemy również przekierowanie użytkownika:
```js
<Route
  path="/"
  element={<Navigate to="/login" replace />}
/>
```
Po wejściu na adres główny użytkownik zostanie automatycznie przekierowany do widoku logowania.

## Formularze logowania i rejestracji
W tym laboratorium dodajemy dwa formularze frontendowe: formularz logowania i formularz rejestracji. Oba formularze przechowują wartości pól w stanie komponentu, blokują domyślne przeładowanie strony po wysłaniu formularza, wysyłają request do backendu i reagują na odpowiedź API.

W React wartości wpisywane przez użytkownika przechowujemy za pomocą useState. Przykładowo w formularzu logowania przechowywany jest email, hasło, informacja o błędzie oraz informacja o trwającym requestcie.

```js
// frontend/src/pages/LoginPage.jsx

const [email, setEmail] = useState("");
const [password, setPassword] = useState("");
const [error, setError] = useState("");
const [loading, setLoading] = useState(false);
```
Podczas wysłania formularza React wykonuje funkcję handleSubmit. Pierwszym krokiem jest wywołanie `event.preventDefault()`, które blokuje klasyczne przeładowanie strony przez przeglądarkę.
```js
// frontend/src/pages/LoginPage.jsx

async function handleSubmit(event) {
  event.preventDefault();

  setError("");
  setLoading(true);

  try {
    await apiPost("/auth/login", {
      email: email,
      password: password,
    });

    navigate("/dashboard");
  } catch (err) {
    setError(err.message);
  } finally {
    setLoading(false);
  }
}
```
W tym fragmencie frontend wysyła dane logowania do endpointu `POST /auth/login`. Jeżeli backend poprawnie zaloguje użytkownika, ustawia cookie `auth_token`, a React przekierowuje operatora do widoku `/dashboard`. Jeżeli backend zwróci błąd, komunikat zostanie zapisany w stanie error i wyświetlony w formularzu.


Formularz rejestracji działa analogicznie, ale zawiera większą liczbę pól. Wysyła dane do endpointu POST `/auth/register`.

## Navbar i podstawowy layout aplikacji
Wraz ze wzrostem liczby widoków pojawia się potrzeba wprowadzenia elementów współdzielonych przez różne interfejsy. W React często realizuje się to przez osobne komponenty wielokrotnego użytku. W naszym projekcie tworzymy komponent Navbar, który będzie odpowiadał za nawigację między widokami dla zalogowanego użytkownika. 

```js
// frontend/src/components/Navbar.jsx

import { Link, useNavigate } from "react-router-dom";

import { apiPost } from "../api/client";

function Navbar() {
  const navigate = useNavigate();

  async function handleLogout() {
    try {
      await apiPost("/auth/logout", {});
    } catch (err) {
      console.error(err);
    } finally {
      navigate("/login");
    }
  }

  return (
    <nav className="navbar">
      <div className="navbar-links">
        <Link to="/dashboard">Dashboard</Link>
        <Link to="/students">Studenci</Link>
        <Link to="/draft">Robocza grupa</Link>
      </div>

      <button onClick={handleLogout}>
        Wyloguj
      </button>
    </nav>
  );
}

export default Navbar;
```
Do przechodzenia pomiędzy widokami wykorzystujemy komponent `<Link />`. W przeciwieństwie do klasycznego znacznika HTML `<a>`, przejście pomiędzy stronami korzystając z `Link` odbywa się bez przeładowywania strony.

Komponent `Navbar` jest następnie wykorzystywany w wielu widokach aplikacji:
```js
<>
  <Navbar />

  <main>
    ...
  </main>
</>
```

## Protected Routes
W tworzonej aplikacji występują widoki które powinny być dostępne tylko dla zalogowanego użytkownika. Sprawdzanie sesji mogłoby zostać zaimplementowane osobno w każdym komponencie React. Wraz ze wzrostem liczby widoków prowadziłoby to jednak do powielania tej samej logiki w wielu miejscach aplikacji, więc wprowadzony został komponent `ProtectedRoute.jsx`.

```js
// frontend/src/components/ProtectedRoute.jsx

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
```

Komponent wykorzystuje wcześniej przygotowany hook `useCurrentOperator`. **Hooki (hooks)** w React służą do współdzielenia logiki między komponentami. Dzięki nim można przenieść powtarzający się kod do osobnych funkcji i używać go w wielu miejscach. Można powiedzieć, że komponent odpowiada za to co widać na ekranie, a hook za to jak działa dana logika.

W naszym projekcie hook `useCurrentOperator` odpowiada za wykonanie requestu `GET /auth/me`, sprawdzenie aktywnej sesji użytkownika, pobranie danych aktualnego operatora oraz przekierowanie do `/login` w przypadku braku sesji.
```js
// frontend/src/hooks/useCurrentOperator.js

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { apiGet } from "../api/client";

function useCurrentOperator() {
  const navigate = useNavigate();

  const [operator, setOperator] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [authError, setAuthError] = useState("");

  useEffect(() => {
    async function loadCurrentOperator() {
      try {
        const data = await apiGet("/auth/me");
        setOperator(data);
      } catch (err) {
        setAuthError(err.message);
        navigate("/login");
      } finally {
        setAuthLoading(false);
      }
    }

    loadCurrentOperator();
  }, [navigate]);

  return {
    operator,
    authLoading,
    authError,
  };
}

export default useCurrentOperator;
```

Jeżeli backend potwierdzi aktywną sesję użytkownika, hook zwraca dane operatora oraz pozwala renderować chroniony widok:
```js
return children;
```
Natomiast jeśli użytkownik nie ma aktywnej sesji, następuje przekierowanie do podstrony `/login`

Protected Route wykorzystujemy bezpośrednio w routingu aplikacji:
```js
<Route
  path="/students"
  element={
    <ProtectedRoute>
      <StudentsPage />
    </ProtectedRoute>
  }
/>
```

## Dashboard i lista studentów
Po skonfigurowaniu logowania i ochrony tras dodane zostały pierwsze widoki dostępne dla zalogowanego operatora. Dashboard pełni rolę prostego widoku startowego po zalogowaniu, natomiast widok studentów pokazuje listę studentów pobraną z backendu. W `StudentsPage.jsx` wykorzystujemy `useEffect`, aby po wejściu na stronę pobrać dane z endpointu `GET /students`.

```js
// frontend/src/pages/StudentsPage.jsx

useEffect(() => {
  async function loadData() {
    const studentsData = await apiGet("/students");
    const draftData = await apiGet("/assignments/draft");

    setStudents(studentsData);
    setDraft(draftData);
  }

  loadData();
}, []);
```
Pobrana lista studentów jest następnie renderowana w JSX za pomocą metody `map`.
```js
// frontend/src/pages/StudentsPage.jsx

{filteredStudents.map((student) => (
  <article key={student.id} className="student-item">
    <div>
      <strong>
        {student.name} {student.lastname}
      </strong>

      <p>Nr albumu: {student.student_code}</p>
      <p>Email: {student.email}</p>
      <p>ECTS: {student.ects_points}</p>
      <p>Kierunek: {student.field_of_study.name}</p>
      <p>Wydział: {student.field_of_study.faculty.name}</p>
    </div>
  </article>
))}
```

Warto zwrócić uwagę, że frontend korzysta tutaj z danych zagnieżdżonych zwracanych przez backend. Nazwa kierunku pobierana jest z `student.field_of_study.name`, a nazwa wydziału z `student.field_of_study.faculty.name`.

## Filtrowanie studentów
Widok listy studentów został dodatkowo rozszerzony o proste filtrowanie po wydziale oraz kierunku studiów. Nie dodajemy do tego osobnych endpointów backendowych, ponieważ wszystkie potrzebne dane znajdują się już w odpowiedzi z `GET /students`. Frontend wyciąga unikalne nazwy wydziałów i kierunków z pobranej listy studentów, a następnie wykorzystuje je do zbudowania pól **select**.

```js
// frontend/src/pages/StudentsPage.jsx

const faculties = useMemo(() => {
  return [
    ...new Set(
      students.map((student) => student.field_of_study.faculty.name)
    ),
  ];
}, [students]);
```
W tym fragmencie `students.map()` pobiera nazwy wydziałów z obiektów studentów, a `Set` usuwa powtarzające się wartości. Dzięki temu w filtrze każdy wydział pojawia się tylko raz. Lista kierunków jest budowana analogicznie. 
```js
// frontend/src/pages/StudentsPage.jsx

const fieldsOfStudy = useMemo(() => {
  return [
    ...new Set(
      students
        .filter((student) => {
          if (selectedFaculty === "ALL") {
            return true;
          }

          return student.field_of_study.faculty.name === selectedFaculty;
        })
        .map((student) => student.field_of_study.name)
    ),
  ];
}, [students, selectedFaculty]);
```
Lista kierunków zależy od wybranego wydziału. Jeżeli wybierzemy konkretny wydział, w drugim filtrze pojawią się tylko kierunki należące do tego wydziału.

Hook `useMemo` sprawia, że dane pochodne, takie jak lista wydziałów, lista kierunków oraz przefiltrowana lista studentów, są przeliczane tylko wtedy, gdy zmienią się zależności, np. lista studentów lub wybrane filtry.
```js
// frontend/src/pages/StudentsPage.jsx

const filteredStudents = useMemo(() => {
  return students.filter((student) => {
    const matchesFaculty =
      selectedFaculty === "ALL" ||
      student.field_of_study.faculty.name === selectedFaculty;

    const matchesField =
      selectedField === "ALL" ||
      student.field_of_study.name === selectedField;

    return matchesFaculty && matchesField;
  });
}, [students, selectedFaculty, selectedField]);
```

## Obsługa roboczej grupy studentów (koszyka)
Dodawanie studenta odbywa się z poziomu widoku listy studentów. Po kliknięciu przycisku **Dodaj do grupy** frontend wysyła request `POST /assignments/draft/items` z identyfikatorem danego studenta. 
```js
// frontend/src/pages/StudentsPage.jsx

await apiPost("/assignments/draft/items", {
  student_id: studentId,
});
```
Po poprawnym dodaniu studenta frontend ponownie pobiera dane studentów oraz aktualny draft. Dzięki temu przycisk przy dodanym studencie zostaje zablokowany i zmienia treść na "Dodano do grupy".
```js
// frontend/src/pages/StudentsPage.jsx

<button
  disabled={isAdded}
  className={isAdded ? "added-button" : ""}
  onClick={() => handleAddToDraft(student.id)}
>
  {isAdded ? "Dodano do grupy" : "Dodaj do grupy"}
</button>
```
Podgląd roboczej grupy znajduje się w widoku DraftPage.jsx. Frontend pobiera dane z endpointu `GET /assignments/draft` i wyświetla liczbę studentów, sumę punktów ECTS oraz listę pozycji draftu. 

```js
// frontend/src/pages/DraftPage.jsx
const data = await apiGet("/assignments/draft");
setDraft(data);
```
Po usunięciu pozycji widok draftu jest ponownie odświeżany, dzięki czemu operator od razu widzi aktualny stan draftu.
```js
// frontend/src/pages/DraftPage.jsx

await apiDelete(`/assignments/draft/items/${itemId}`);
await loadDraft();
```

## Zadanie do wykonania na laboratorium
W ramach laboratorium należy uruchomić backend oraz frontend projektu, sprawdzić komunikację pomiędzy React i FastAPI, a następnie przejść przez podstawowy proces użytkownika w aplikacji.
Wykonaj poniższe kroki:
1. Aktywuj środowisko wirtualne backendu:<br>
  `.venv\Scripts\activate`
2. Uruchom kontenery projektu za pomocą polecenia:<br>
  `docker compose up -d --build`
3. Uruchom backend FastAPI poleceniem:<br>
  `uvicorn main:app --reload`
4. Sprawdź, czy masz zainstalowane Node.js oraz npm:<br>
  `node -v`<br>
  `npm -v`
5. Jeżeli folder frontend nie został jeszcze utworzony, wykonaj w głównym katalogu projektu:<br>
  `npx create-react-app frontend`<br>
  Przejdź do folderu frontendu:<br>
  `cd frontend`
6. Zainstaluj zależności frontendu:
  `npm install`
7. Uruchom frontend React:
  `npm start`
8. Frontend powinien być dostępny pod adresem:<br>
  `http://localhost:3000`
9. Zarejestruj operatora i zaloguj się do aplikacji.
10. Sprawdź działanie dashboardu i protected routes.
11. Zweryfikuj:
* pobieranie listy studentów,
* filtrowanie po wydziale i kierunku,
* dodawanie studentów do draftu.
12. Przejdź do widoku roboczej grupy i sprawdź:
* liczbę studentów,
* sumę ECTS,
* usuwanie studentów z draftu,
* działanie logoutu.


## Projekt 4. Etap 1. 
1. Utworzenie aplikacji frontendowej w React oraz połączenie jej z backendem sklepu internetowego. Frontend powinien zostać umieszczony w osobnym folderze `frontend`, uruchamiany przez npm start i komunikować się z backendem przez REST API. Należy skonfigurować routing, wspólny klient API oparty o fetch, obsługę cookie sesyjnego oraz protected routes dla widoków dostępnych tylko po zalogowaniu. 
2. Implementacja podstawowego flow użytkownika w sklepie. Aplikacja powinna umożliwiać rejestrację, logowanie, wylogowanie, pobranie aktualnego użytkownika, wyświetlenie listy produktów oraz filtrowanie produktów po wybranych cechach, np. kategorii lub producencie. Widok produktów powinien umożliwiać dodanie produktu do koszyka wraz z określeniem liczby sztuk. Dodanie produktu nie powinno blokować możliwości dodania kolejnych sztuk tego samego produktu, o ile nie przekracza to dostępnego stanu magazynowego.
3. Implementacja widoku koszyka. Użytkownik powinien widzieć produkty znajdujące się w koszyku, liczbę sztuk każdego produktu, cenę jednostkową, cenę pozycji oraz sumę całego koszyka. W koszyku powinna istnieć możliwość zmniejszenia liczby sztuk produktu, zwiększenia liczby sztuk produktu oraz usunięcia produktu z koszyka. Frontend powinien odświeżać widok po każdej operacji i poprawnie reagować na błędy zwracane przez backend, np. próbę dodania większej liczby sztuk niż dostępna w magazynie.