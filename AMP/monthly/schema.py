from typing import Literal

from pydantic import BaseModel, Field

class AMPMonthlySchema(BaseModel):
    # Forbid extra fields not defined in the schema
    model_config = {
        "extra": "forbid",
    }
    # Define each column. Headers with spaces or special characters are handled using the Field alias.
    Labeler_Name: str = Field(alias="Labeler Name")
    NDC: str = Field(min_length=11, max_length=11)
    FDA_Product_Name: str = Field(alias="FDA Product Name")
    Status: str
    Year: str = Field(min_length=4, max_length=4)
    Month: Literal["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]