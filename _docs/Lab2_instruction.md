
# LABORATORIUM 2

## Implementacja operacji CRUD w architekturze warstwowej

Podstawą niemal każdego systemu informatycznego jest zestaw operacji CRUD (Create, Read, Update, Delete). W architekturze REST każda z tych operacji znajduje swoje bezpośrednie odzwierciedlenie w metodach protokołu HTTP.

| Operacja | Metoda HTTP | Znaczenie |
|--------|-------------|-----------|
| Create | POST | tworzenie zasobu |
| Read | GET | odczyt zasobu |
| Update | PUT / PATCH | aktualizacja zasobu |
| Delete | DELETE | usunięcie zasobu |


## Przypomnienie z poprzedniego laboratorium

Nasze rozwiązanie opiera się na separacji odpowiedzialności:
* Model: Definicje struktur danych (Pydantic dla walidacji i SQLAlchemy dla bazy danych).
* Data (Repository): Czyste operacje na bazie danych (SQLAlchemy).
* Service: Logika biznesowa, walidacje domenowe i koordynacja pracy.
* Web: Obsługa protokołu HTTP, definicja endpointów i statusów odpowiedzi.

## Rozbudowa modelu danych i relacje
Do dzisiejszego laboratorium, będziemy potrzebowali bardziej rozbudowanej bazy danych. Przejdziemy również po implementacji relacji między tabelami. Schemat bazy danych na której będziemy pracować wygląda następująco:<br>
![alt text](images/image.png)

## Implementacja metod CRUD - część 2
### GET - pobieranie wszystkich studentów

Podczas pobierania list rekordów powiązanych z innymi tabelami (np. student i jego kierunek), kluczowym wyzwaniem jest optymalizacja liczby zapytań do bazy danych. Domyślnie systemy ORM często stosują tzw. Lazy Loading, co prowadzi do problemu zapytania $N+1$.

Problem $N+1$ w pigułce:<br>
Wyobraź sobie, że pobierasz listę 100 studentów jednym zapytaniem. Jeśli chcesz wyświetlić również ich wydziały, a system nie został zoptymalizowany, ORM wykona 1 zapytanie po studentów oraz 100 dodatkowych zapytań (po jednym dla każdego studenta), aby dociągnąć dane o wydziale. To drastycznie spowalnia aplikację.

Aby temu zapobiec, stosujemy Eager Loading (ładowanie zachłanne) za pomocą funkcji `joinedload`. Informuje ona SQLAlchemy, aby pobrało wszystkie powiązane dane już w pierwszym zapytaniu, wykorzystując operator SQL JOIN.

#### Warstwa danych
W warstwie danych musimy wskazać, że chcemy dociągnąć informacje o kierunku studiów i wydziale.
```python
#data/student_repository.py
def get_all_students(db: Session):
    query = (
        select(StudentORM)
        .options(
            joinedload(StudentORM.field_of_study)#informacje o kierunku
            .joinedload(FieldOfStudyORM.faculty)#informacje o wydziale
        )
    )
    result = db.execute(query)
    return result.scalars().all()
```

#### Warstwa modelu i service
Aby przesłać zagnieżdżone dane do klienta, musimy odpowiednio przygotować schematy Pydantic.

```python
#service/student_service.py
def list_students(db: Session):
    # Pobranie listy wszystkich studentów z repozytorium
    return get_all_students(db)

```
```python
#model/student_schema
class Faculty(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class FieldOfStudy(BaseModel):
    id: int
    name: str
    min_ects: int
    max_ects: int
    faculty: Faculty

    class Config:
        from_attributes = True

class Student(BaseModel):
    id: int
    name: str
    lastname: str
    email: EmailStr
    ects_points: int
    field_of_study: FieldOfStudy

    class Config:
        from_attributes = True
```

```python
# web/routes.py
@router.get("/students", response_model=list[Student])
def get_students(db: Session = Depends(get_db)):
    # Pobranie listy wszystkich studentów - domyślnie zwraca status 200 OK
    return list_students(db)
```
### GET - pobierz wybranego studenta

Pobieranie konkretnego zasobu różni się od pobierania listy zastosowaniem filtrowania oraz parametrów ścieżki. Zamiast całej kolekcji, system wyszukuje unikalny rekord na podstawie jego identyfikatora.

```python
#data/student_repository.py
def get_student_by_id(db: Session, student_id: int):
    query = (
        select(StudentORM)
        .where(StudentORM.id == student_id)
        .options(
            joinedload(StudentORM.field_of_study)
            .joinedload(FieldOfStudyORM.faculty)
        )
    )
    result = db.execute(query)
    return result.scalars().first()

```
Dzięki filtrowaniu `.where` zapytanie SQL ogranicza wynik tylko do jednego wiersza o pasującym kluczu głównym.<br>
Nawet przy pobieraniu jednego studenta stosujemy `joinedload`, aby od razu posiadać komplet informacji o jego kierunku i wydziale bez dodatkowych zapytań do bazy.

```python
#service/student_service.py
def get_student(db: Session, student_id: int):
    # Pobranie konkretnego studenta po ID
    return get_student_by_id(db, student_id)
```

```python
# web/routes.py
@router.get("/students/{id}", response_model=Student)
def get_student_by_id_endpoint(id: int, db: Session = Depends(get_db)):
    student = get_student(db, id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return student
```
### POST (Create)
Metoda **POST** służy do tworzenia nowych zasobów w systemie. W architekturze REST operacja ta nie jest idempotentna (każde żądanie skutkuje utworzeniem nowego obiektu w bazie danych).


#### Warstwa Modelu (Schemat wejściowy)
Zamiast pełnego modelu studenta, używamy klasy StudentCreate. Pozwala to na walidację danych (np. formatu e-mail) bez konieczności przesyłania pól generowanych automatycznie przez bazę, takich jak id.
```python
#model/student_schema
class StudentCreate(BaseModel):
    name: str
    lastname: str
    email: EmailStr
    field_of_study_id: int
    ects_points: int
```

#### Warstwa Serwisu (Logika i Mapowanie)
Serwis odpowiada za mapowanie danych ze schematu Pydantic na obiekt mapowania relacyjnego (ORM). Jest to również miejsce na implementację walidacji.
```python
#service/student_service.py
def create_student(db: Session, payload: StudentCreate):
    #miejsce na walidację
    #miejsce na obsługę błędów
    student = StudentORM(
        name=payload.name,
        lastname=payload.lastname,
        email=payload.email,
        field_of_study_id=payload.field_of_study_id,
        ects_points=payload.ects_points,
    )
    return add_student(db, student)
```

#### Warstwa Danych
Repozytorium zarządza cyklem życia obiektu w sesji. Wykonanie `commit()` jest niezbędne do trwałego zapisania zmian, a `refresh()` pozwala odczytać dane wygenerowane przez bazę (np. nowy klucz główny).
```python
#data/student_repository.py
def add_student(db: Session, student: StudentORM):
    db.add(student)
    db.commit()
    db.refresh(student)
    return student
```

#### Warstwa Web (Endpoint)
Definicja punktu styku z klientem. Zgodnie ze standardem, poprawne utworzenie zasobu zwraca status 201 Created.

```python
# web/routes.py
@router.post("/students", response_model=Student, status_code=201)
def post_student(payload: StudentCreate, db: Session = Depends(get_db)):
    #miejsce na obsługę błędów
    return create_student(db, payload)
```
### PUT (Update)
Metoda **PUT** służy do pełnego zastąpienia istniejącego zasobu nową wersją danych. Zgodnie z założeniami architektury REST, operacja ta jest idempotentna, a więc wielokrotne wykonanie identycznego żądania przyniesie taki sam skutek dla stanu serwera, jak wykonanie go tylko raz.

W praktyce oznacza to, że klient przesyła kompletny obiekt, a serwer nadpisuje wszystkie jego pola wartościami z żądania.

#### Warstwa Danych
Zanim dokonamy aktualizacji, musimy upewnić się, że dany rekord istnieje w bazie. Repozytorium dostarcza metodę wyszukującą obiekt po kluczu głównym.
```python
#data/student_repository.py
def get_student_by_id(db: Session, student_id: int):
    query = select(StudentORM).where(StudentORM.id == student_id)
    result = db.execute(query)
    return result.scalars().first()
```

#### Warstwa Serwisu 
Serwis pobiera istniejący obiekt ORM i przypisuje mu wszystkie wartości przesłane w payload. Jeśli zasób nie zostanie odnaleziony, usługa zwraca None, co pozwala warstwie Web na wygenerowanie błędu 404.
```python
#service/student_service.py
def replace_student(db: Session, student_id: int, payload: StudentCreate):
    student = get_student_by_id(db, student_id)
    #miejsce na walidację
    #miejsce na obsługę błędów
    if student is None:
        return None

    student.name = payload.name
    student.lastname = payload.lastname
    student.email = payload.email
    student.field_of_study_id = payload.field_of_study_id
    student.ects_points = payload.ects_points

    return save_student(db, student)
```

#### Warstwa Web
Endpoint definiuje parametr ścieżki `{id}` oraz przyjmuje schemat StudentCreate. Wykorzystanie tego samego schematu co przy operacji POST wymusza na kliencie przesłanie pełnego zestawu danych niezbędnych do zdefiniowania studenta.

```python
# web/routes.py
@router.put("/students/{id}", response_model=Student)
def put_student(id: int, payload: StudentCreate, db: Session = Depends(get_db)):
    student = replace_student(db, id, payload)
    #miejsce na obsługę błędów
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return student
```
### PATCH (częściowa aktualizacja)
W przeciwieństwie do metody **PUT**, która zastępuje cały zasób, metoda **PATCH** służy do modyfikacji tylko wybranych pól obiektu. Jest to rozwiązanie bardziej wydajne w sytuacjach, gdy chcemy zmienić pojedynczą informację (np. tylko nazwisko studenta), nie przesyłając ponownie wszystkich jego danych do serwera.

#### Warstwa Modelu 
W schemacie StudentUpdate wszystkie pola są zdefiniowane jako opcjonalne (z wartością domyślną None). Dzięki temu klient może wysłać dowolny podzbiór danych, a Pydantic nie odrzuci żądania z powodu brakujących kluczy.
```python
#model/student_schema
class StudentUpdate(BaseModel):
    name: str | None = None
    lastname: str | None = None
```

#### Warstwa Serwisu
To w tej warstwie zapada decyzja, które dane w bazie zostaną nadpisane. Serwis pobiera aktualny stan obiektu z bazy, a następnie sprawdza każde pole przesłane w payload. Jeśli wartość jest inna niż None, aktualizuje odpowiedni atrybut obiektu ORM.

```python
#service/student_service.py
def patch_student(db: Session, student_id: int, payload: StudentUpdate):
        
    #miejsce na obsługę błędów
    student = get_student_by_id(db, student_id)

    #miejsce na walidację
    if student is None:
        return None
    if payload.name is not None:
        student.name = payload.name
    if payload.lastname is not None:
        student.lastname = payload.lastname
    if payload.email is not None:
        student.email = payload.email
    if payload.field_of_study_id is not None:
        student.field_of_study_id = payload.field_of_study_id
    if payload.ects_points is not None:
        student.ects_points = payload.ects_points

    return save_student(db, student)
```

#### Warstwa Web (Endpoint PATCH)
Endpoint korzysta z metody `@router.patch`. `response_model` to nadal pełny model `Student`. Po częściowej aktualizacji klient powinien otrzymać pełny, zaktualizowany obraz zasobu.

```python
# web/routes.py
@router.patch("/students/{id}", response_model=Student)
def patch_student_endpoint(id: int, payload: StudentUpdate, db: Session = Depends(get_db)):
    #miejsce na obsługę błędów
    student = patch_student(db, id, payload)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return student
```
### DELETE
Metoda **DELETE** służy do trwałego usunięcia zasobu identyfikowanego przez konkretny adres URL. Zgodnie ze standardem REST, operacja ta jest idempotentna – wielokrotne usunięcie tego samego zasobu nie powinno zmieniać stanu bazy danych bardziej niż pierwsze wywołanie.

#### Warstwa Danych
Metoda `db.delete()` oznacza obiekt do usunięcia, a `db.commit()` finalizuje operację na dysku.
```python
#data/student_repository.py
def delete_student(db: Session, student: StudentORM):
    db.delete(student)
    db.commit()
```

#### Warstwa Serwisu
Zadaniem serwisu jest koordynacja procesu: najpierw próbujemy odnaleźć rekord, a dopiero po potwierdzeniu jego istnienia wywołujemy procedurę usunięcia. Zapobiega to próbom usuwania nieistniejących danych.
```python
# service/student_service.py
def remove_student(db: Session, student_id: int):
    student = get_student_by_id(db, student_id)
    if student is None:
        return False

    delete_student(db, student)
    return True
```

#### Warstwa Web
```python
# web/routes.py
@router.delete("/students/{id}", status_code=204)
def delete_student_endpoint(id: int, db: Session = Depends(get_db)):
    if not remove_student(db, id):
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Zwracamy czysty Response 204 zgodnie ze standardem REST
    return Response(status_code=204)
```
Zastosowanie statusu 204 No Content to branżowy standard dla operacji usuwania – informuje on klienta, że żądanie zostało przetworzone pomyślnie, a serwer nie przesyła żadnych dodatkowych danych w odpowiedzi. Kluczowym elementem jest tutaj walidacja logiczna: jeśli serwis nie odnalazł zasobu, musimy jawnie zwrócić status 404 Not Found, aby uniknąć błędnego przekonania klienta, że usunięcie nieistniejącego rekordu zakończyło się sukcesem.


## Walidacje

We wcześniejszej części labortorium skupiliśmy się wyłącznie na przepływie danych przez warstwy. W praktyce API musi dodatkowo:
- chronić bazę danych przed zapisem danych niepoprawnych lub niekompletnych
- zapewnić spójność domenową - pilnować zależności między różnymi polami
- informować klienta o błędach w sposób czytelny i ustandaryzowany

### Podział odpowiedzialności (Web vs Service)
Zgodnie z zasadą separacji warstw, walidacje i reguły domenowe umieszczamy w warstwie Service. Jest to miejsce, w którym wymagania biznesowe łączą się z przepływem danych. Warstwa Web (FastAPI) powinna zajmować się wyłącznie protokołem HTTP, a warstwa Data (SQLAlchemy) czystym dostępem do bazy danych.

W profesjonalnej architekturze rozróżniamy dwa poziomy walidacji:
* Walidacja techniczna (syntaktyczna): Wykonywana automatycznie przez FastAPI i bibliotekę Pydantic w warstwie Web. Sprawdza ona  czy typy są zgodne, czy wymagane pola są obecne i czy struktura obiektu JSON jest poprawna.
* Walidacja biznesowa (domenowa): Wykonywana w warstwie Service. Sprawdza ona reguły logiczne systemu, takie jak unikalność numeru albumu czy istnienie powiązanego kierunku studiów w bazie danych.

### Implementacja wyjątków domenowych
Kluczową zasadą projektową jest całkowita izolacja warstwy Service od protokołu HTTP. Oznacza to, że serwis nie powinien rzucać błędów typu HTTPException. Zamiast tego definiujemy własne klasy wyjątków Pythona, które opisują problemy biznesowe. Pozwala to na testowanie logiki niezależnie od tego, czy aplikacja działa jako serwer WWW, czy jako skrypt konsolowy.

```python
# service/student_validators.py
class ValidationError(Exception): # Błędy wartości (np. za krótki kod)
    pass

class ConflictError(Exception): # Błędy unikalności (np. zajęty e-mail)
    pass

class ResourceNotFoundError(Exception): # Błędy braku powiązań (np. brak kierunku)
    pass

def validate_student_code_length(student_code: str):
    if not (5 <= len(student_code) <= 10):
        #Rzucamy wyjątek Pythona, bez kodu HTTP
        raise ValidationError("Numer albumu studenta musi mieć długość od 5 do 10 znaków.")
```

### Relacja walidacji i obsługi błędów (Mapping)
| Wyjątek Domenowy | Kod Statusu HTTP | Znaczenie |
|--------|-------------|-----------|
| ValidationError | 422 Unprocessable Entity | Dane mają poprawny format, ale naruszają reguły systemu |
| ConflictError | 409 Conflict | Operacja koliduje ze stanem bazy (np. zajęty numer albumu) |
| ResourceNotFoundError | 400 Bad Request | Żądanie odwołuje się do nieistniejącej relacji |
| None (wynik funkcji) | 404 Not Found | Zasób nie istnieje pod wskazanym adresem URL |


### Przykład praktyczny (Warstwa Web)
Warstwa Web przechwytuje błędy z serwisu za pomocą bloku try-except i nadaje im kontekst protokołu HTTP. Pozwala to na zachowanie czystej separacji warstw aplikacji.

```python
# web/routes.py

@router.post("/students", response_model=Student, status_code=201)
def post_student(payload: StudentCreate, db: Session = Depends(get_db)):
    # Próba utworzenia nowego zasobu z obsługą wyjątków domenowych
    try:
        # Sukces zwraca status 201 Created
        return create_student(db, payload)
        
    except ValidationError as e:
        # Błędy reguł biznesowych mapujemy na status 422
        raise HTTPException(status_code=422, detail=str(e))
        
    except ConflictError as e:
        # Naruszenie unikalności (np. numeru albumu) mapujemy na 409
        raise HTTPException(status_code=409, detail=str(e))
        
    except ResourceNotFoundError as e:
        # Brak powiązanych zasobów (np. kierunku) mapujemy na 400
        raise HTTPException(status_code=400, detail=str(e))
```


## Implementacja walidacji w operacjach CRUD
### GET `/students/{id}`
Jeśli student o zadanym id nie istnieje, klient powinien otrzymać informację, że nie można go odczytać. Właśnie dlatego po pobraniu studenta z repozytorium sprawdza się, czy wynik nie jest pusty. Jeżeli student nie został znaleziony, zwracany jest `404`.

```python
# service/student_service.py
def get_student(db: Session, student_id: int):
    # Serwis zwraca wynik bezpośrednio z repozytorium
    # Jeśli student nie istnieje, zwróci wartość None
    return get_student_by_id(db, student_id)

# web/routes.py
from fastapi import HTTPException, status

@router.get("/students/{id}", response_model=Student)
def get_student_by_id_endpoint(id: int, db: Session = Depends(get_db)):
    student = get_student(db, id)

    # Jeśli serwis nie zwrócił obiektu, podnosimy błąd 404 Not Found
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Student not found"
        )
    return student
```

### POST `/students`
W tej operacji system przeprowadza wielopoziomową kontrolę, dzieląc reguły na kilka kluczowych obszarów:
* Tożsamość (student_code): Sprawdzamy, czy numer albumu ma od 5 do 10 znaków, czy składa się wyłącznie z liter i cyfr oraz czy jest unikalny w skali całego systemu.
* Weryfikujemy, czy wskazany kierunek studiów istnieje w bazie.
* Sprawdzamy czy liczba punktów ECTS nie jest ujemna oraz czy mieści się w zakresie zdefiniowanym dla konkretnego kierunku.
* Sprawdzamy adres email pod kątem zakazanych fraz

Każda z powyższych walidacji mapuje się na konkretny kod HTTP:
- `409` dla konfliktu unikalności,
- `400` dla nieistniejącego kierunku,
- `422` dla naruszenia reguł walidacyjnych.

```python
# service/student_service.py

def _validate_student_full_data(db: Session, payload: StudentCreate, student_id: int = None):
    """
    Prywatna metoda pomocnicza do pełnej walidacji danych studenta (Zasada DRY).
    Konsoliduje reguły wymagane przy operacjach POST i PUT.
    """
    # Walidacja tożsamości (Numer albumu: długość, znaki, unikalność)
    validate_student_code_length(payload.student_code)
    validate_student_code_alphanumeric(payload.student_code)
    validate_student_code_unique(db, payload.student_code, student_id)
    
    # Walidacja powiązań (Sprawdzenie czy kierunek studiów istnieje w bazie)
    field = validate_field_of_study_exists(db, payload.field_of_study_id)
    
    # Walidacja punktów ECTS (Nieujemność oraz zgodność z zakresem kierunku)
    validate_ects_non_negative(payload.ects_points)
    validate_ects_range(field, payload.ects_points)
    
    # Walidacja polityki systemu (Sprawdzenie e-mail pod kątem zakazanych fraz)
    validate_email_forbidden_phrases(db, payload.email)
    
    return field

def create_student(db: Session, payload: StudentCreate):
    # Wykonanie pełnego zestawu walidacji przed utworzeniem
    _validate_student_full_data(db, payload)

    # Tworzenie obiektu ORM na podstawie przesłanych danych
    student = StudentORM(
        name=payload.name,
        lastname=payload.lastname,
        student_code=payload.student_code,
        email=payload.email,
        field_of_study_id=payload.field_of_study_id,
        ects_points=payload.ects_points,
    )

    # Dodanie studenta do bazy danych przez warstwę repozytorium
    return add_student(db, student)
```
```python
#web/routes.py
@router.post("/students", response_model=Student, status_code=201)
def post_student(payload: StudentCreate, db: Session = Depends(get_db)):
    # Próba utworzenia nowego zasobu z obsługą wyjątków domenowych
    try:
        # Sukces zwraca status 201 Created
        return create_student(db, payload)
        
    except ValidationError as e:
        # Błędy reguł biznesowych mapujemy na status 422
        raise HTTPException(status_code=422, detail=str(e))
        
    except ConflictError as e:
        # Naruszenie unikalności (np. numeru albumu) mapujemy na 409
        raise HTTPException(status_code=409, detail=str(e))
        
    except ResourceNotFoundError as e:
        # Brak powiązanych zasobów (np. kierunku) mapujemy na 400
        raise HTTPException(status_code=400, detail=str(e))
```

### PUT `/students/{id}`
W tej metodzie kluczowa jest kolejność działań. Zanim serwer zacznie tracić zasoby na sprawdzanie poprawności numeru albumu czy punktów ECTS, musimy upewnić się, że mamy co aktualizować.

Dlatego w `PUT` kolejność jest następująca:
1. sprawdzenie, czy student istnieje
2. walidacja przesłanych danych
3. zapis nowego stanu do bazy

W `PUT` klient wysyła całą reprezentację obiektu. Oznacza to, że wszystkie pola muszą zostać uznane za obowiązujące. Z tego powodu walidacja jest analogiczna do tej z `POST`.
```python
# service/student_service.py

def replace_student(db: Session, student_id: int, payload: StudentCreate):
    # Sprawdzenie, czy zasób do aktualizacji (PUT) w ogóle istnieje
    student = get_student_by_id(db, student_id)
    if student is None:
        return None  # Sygnał dla Routes do rzucenia 404

    # Pełna walidacja nowych danych (przekazujemy student_id, by zignorować autokolizję kodu)
    _validate_student_full_data(db, payload, student_id)

    # Nadpisanie wszystkich pól istniejącego obiektu ORM
    student.name = payload.name
    student.lastname = payload.lastname
    student.student_code = payload.student_code
    student.email = payload.email
    student.field_of_study_id = payload.field_of_study_id
    student.ects_points = payload.ects_points

    # Trwałe zapisanie zmian w bazie danych
    return save_student(db, student)
```
```python
# web/routes.py

@router.put("/students/{id}", response_model=Student)
def put_student(id: int, payload: StudentCreate, db: Session = Depends(get_db)):
    # Pełna aktualizacja zasobu (zastąpienie)
    try:
        student = replace_student(db, id, payload)
        # Pierwszym krokiem jest zawsze sprawdzenie, czy główny zasób istnieje
        if student is None:
            raise HTTPException(status_code=404, detail="Student not found")
        return student
        
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
```
---

### PATCH `/students/{id}`
W odróżnieniu od `PUT`, w `PATCH` nie wszystkie pola muszą być obecne. Dlatego walidujemy wyłącznie te pola, które rzeczywiście pojawiły się w żądaniu.

Przykłady:
- jeśli klient przesyła tylko `student_code`, sprawdzamy długość, znaki i unikalność wyłącznie tego pola,
- jeśli klient przesyła `ects_points`, sprawdzamy nieujemność i zakres,
- jeśli klient przesyła `field_of_study_id`, sprawdzamy istnienie kierunku.

Metoda `PATCH` jest szczególnie interesująca z punktu widzenia zależności między walidacją a stanem obiektu. Jeśli klient aktualizuje punkty ECTS, ale nie zmienia kierunku, walidacja musi korzystać z dotychczasowego kierunku studenta. Jeśli natomiast zmienia kierunek, walidacja zakresu ECTS musi odnosić się do nowego kierunku.

Oznacza to, że `PATCH` nie waliduje wyłącznie samego payloadu, lecz również jego relację z istniejącym stanem rekordu.

```python
# service/student_service.py

def patch_student(db: Session, student_id: int, payload: StudentUpdate):
    # Weryfikacja istnienia głównego zasobu do częściowej aktualizacji
    student = get_student_by_id(db, student_id)
    if student is None:
        return None

    # Warunkowa walidacja numeru albumu (tylko jeśli klient przesłał to pole)
    if payload.student_code is not None:
        validate_student_code_length(payload.student_code)
        validate_student_code_alphanumeric(payload.student_code)
        validate_student_code_unique(db, payload.student_code, student_id)
        student.student_code = payload.student_code

    # Inteligentny wybór kierunku do walidacji zakresu punktów ECTS
    # Jeśli klient zmienia kierunek - bierzemy nowy, jeśli nie - bierzemy obecny z bazy
    field_id_to_validate = payload.field_of_study_id or student.field_of_study_id
    field = validate_field_of_study_exists(db, field_id_to_validate)
    
    # Walidacja ECTS (zawsze sprawdzana względem poprawnego kontekstu kierunku)
    if payload.ects_points is not None:
        validate_ects_non_negative(payload.ects_points)
        validate_ects_range(field, payload.ects_points)
        student.ects_points = payload.ects_points

    # Sprawdzenie polityki email i aktualizacja pozostałych pól tekstowych
    if payload.email is not None:
        validate_email_forbidden_phrases(db, payload.email)
        student.email = payload.email

    if payload.name is not None:
        student.name = payload.name
    if payload.lastname is not None:
        student.lastname = payload.lastname
    if payload.field_of_study_id is not None:
        student.field_of_study_id = payload.field_of_study_id

    # Zapisanie częściowych zmian
    return save_student(db, student)
```
```python
# web/routes.py
@router.patch("/students/{id}", response_model=Student)
def patch_student_endpoint(id: int, payload: StudentUpdate, db: Session = Depends(get_db)):
    # Częściowa aktualizacja zasobu
    try:
        student = patch_student(db, id, payload)
        # Podobnie jak w PUT, brak zasobu skutkuje błędem 404
        if student is None:
            raise HTTPException(status_code=404, detail="Student not found")
        return student
        
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
```


### DELETE `/students/{id}`
Kluczowym warunkiem poprawności jest istnienie zasobu. Jeżeli student nie istnieje, system powinien zwrócić `404`, ponieważ nie można usunąć czegoś, czego nie ma w bazie.

```python
# service/student_service.py
def remove_student(db: Session, student_id: int):
    # Sprawdzenie, czy student do usunięcia istnieje w bazie
    student = get_student_by_id(db, student_id)

    if student is None:
        # Sygnał dla warstwy Web: nie można usunąć czegoś, czego nie ma
        return False

    # Wywołanie fizycznego usunięcia rekordu w warstwie danych
    delete_student(db, student)

    # Zwrócenie sukcesu operacji (Web Layer odpowie statusem 204)
    return True
```
```python
# web/routes.py
@router.delete("/students/{id}", status_code=204)
def delete_student_endpoint(id: int, db: Session = Depends(get_db)):
    # Próba usunięcia zasobu
    # Serwis zwraca wartość logiczną informującą o sukcesie operacji
    if not remove_student(db, id):
        # Jeśli zasób nie istniał, informujemy o tym klienta (404)
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Przy sukcesie zwracamy status 204 No Content bez treści w body odpowiedzi
    return Response(status_code=204)
```


## Zadanie do wykonania na laboratorium
Uruchom program przestawiający standardową warstwową architekture REST w katalogu ./REST. Wykonaj poniższe kroki:

1. Aktywuj środowisko wirtualne

`python -m venv venv`  

`.\venv\Scripts\activate` 

`pip install -r .\requirements.txt`

2. Uruchom dockera i uruchom kontener

`docker compose up`

3. Nawiąż połączenie z bazą danych za pomocą rozszerzenia w VSC Postgres od firmy Microsoft.
([link](https://marketplace.visualstudio.com/items?itemName=ms-ossdata.vscode-pgsql)).

Uzupełnij dane wg poniższego wzoru:

![alt text](images/new_connection_postgres.png)

4. Usuń starą nieaktualną bazę danych. Powstały skrypt aktywuj zieloną strzałką. 

![alt text](images/drop_table.png)

5. Uruchom plik `REST/db/init/001_init.sql` za pomocą zielonej strzałki

5. Uruchom FastApi
`uvicorn main:app --reload`
6. Przeanalizuj dokładnie kod umieszczony w katalogu REST - zwłaszcza część dot. walidacji i obsługi błędów
7. Przetestuj działanie endpointów pod adresem: [http://127.0.0.1:8000/docs#](http://127.0.0.1:8000/docs#)


## Etap 2. Projekt 1.
- aktualizacja bazy danych o dodatkową tabelę zawierające kategorie oraz tabelę z listą zakazanych nazw
- Utwórz w oparciu o architekturę warstwową REST - endpoint: 
    - `GET /api/v1/products`
    - `GET /api/v1/products/{id}`
    - `POST /api/v1/products`
    - `PUT /api/v1/products/{id}` 
    - `DELETE /api/v1/products/{id}`.
- Utwórz następujące walidacje: 
    - nazwa unikalna (3–20 znaków, litery/cyfry)
    - cena w widełkach zależnych od kategorii
    - w szczegółach produktu zwracana ilość dostępnych sztuk (≥ 0)
