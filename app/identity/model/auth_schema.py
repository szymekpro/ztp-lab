from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class OperatorResponse(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=256)
    confirm_password: str = Field(..., min_length=1, max_length=256)
    first_name: str= Field(..., min_length=1, max_length=256)
    last_name: str = Field(..., min_length=1, max_length=256)

    @model_validator(mode="after")
    def validate_matching_passwords(self):
        if self.password != self.confirm_password:
            raise ValueError("Hasło i potwierdzenie hasła muszą być takie same.")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    operator: OperatorResponse