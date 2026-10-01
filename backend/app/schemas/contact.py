from pydantic import BaseModel, Field


class ContactMessage(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=6, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    subject: str = Field(min_length=3, max_length=150)
    message: str = Field(min_length=10, max_length=2000)
