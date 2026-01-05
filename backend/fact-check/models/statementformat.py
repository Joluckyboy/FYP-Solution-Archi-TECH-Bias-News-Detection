from pydantic import BaseModel

class StatementFormat(BaseModel):
    statement: str