# Define your schema using Pydantic
from datetime import date
import math
from pydantic import BaseModel, Field, field_validator
from typing import Literal

class NADACComparisonSchema(BaseModel):
    # Forbid extra fields not defined in the schema
    model_config = {
        "extra": "forbid",
    }
    # Define each column. Headers with spaces or special characters are handled using the Field alias.
    NDC_Description: str = Field(alias="NDC Description")
    NDC: str = Field(min_length=11, max_length=11)
    Old_NADAC_Per_Unit: float = Field(alias="Old NADAC Per Unit")
    New_NADAC_Per_Unit: float = Field(alias="New NADAC Per Unit")
    Classification_for_Rate_Setting: str = Field(alias="Classification for Rate Setting")
    Percent_Change: float = Field(alias="Percent Change")
    Primary_Reason: str | None = Field(alias="Primary Reason")
    Start_Date: date = Field(alias="Start Date")
    End_Date: date = Field(alias="End Date")
    Effective_Date: date | None = Field(alias="Effective Date")
    
    # Clean up 'nan' values. Convert to 'None' for optional fields.
    @field_validator("Effective_Date", "Primary_Reason", mode="before")
    def nan_to_none(cls, v):
        if isinstance(v, float) and math.isnan(v):
            return None
        return v

    @field_validator("New_NADAC_Per_Unit", "Old_NADAC_Per_Unit")
    def five_decimal_places(cls, v: float) -> float:
        if v is None:
            return v
        if round(v, 5) != v:
            raise ValueError("Field must have 5 decimal places")
        return v
    
    @field_validator("Percent_Change")
    def two_decimal_places(cls, v: float) -> float:
        if v is None:
            return v
        if round(v, 2) != v:
            raise ValueError("Field must have 2 decimal places")
        return v

    @field_validator('Effective_Date', mode='before')
    def parse_custom_date_with_NaN(cls, v: date | None):
        if v is None:
            return v
        if isinstance(v, float) and math.isnan(v):
            return v
        if isinstance(v, str):
            # Parse from "MM/DD/YYYY" to a date object
            return date.strptime(v, "%m/%d/%Y")
        return v

    @field_validator('Start_Date', 'End_Date', mode='before')
    def parse_custom_date(cls, v: date):
        if isinstance(v, float) and math.isnan(v):
            return v
        if isinstance(v, str):
            # Parse from "MM/DD/YYYY" to a date object
            return date.strptime(v, "%m/%d/%Y")
        return v