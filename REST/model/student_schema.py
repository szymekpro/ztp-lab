from pydantic import BaseModel


class Student(BaseModel):
    id: int
    name: str
    lastname: str

    class Config:
        # Umożliwia Pydanticowi mapowanie danych bezpośrednio z atrybutów obiektów (np. student.name) 
        # zamiast tylko ze słowników (np. student["name"]). Jest to niezbędne, aby model mógł 
        # automatycznie "przepisać" dane z instancji klasy StudentORM na schemat JSON.
        from_attributes = True