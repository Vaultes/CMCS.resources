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
    Percent_Change: str = Field(alias="Percent Change")
    Primary_Reason: str = Field(alias="Primary Reason")
    Start_Date: date = Field(alias="Start Date")
    End_Date: date = Field(alias="End Date")
    Effective_Date: date = Field(alias="Effective Date")

    @field_validator('Start_Date', 'End_Date', 'Effective_Date', mode='before')
    def parse_custom_date(cls, v):
        if isinstance(v, float) and math.isnan(v):
            return v
        if isinstance(v, str):
            # Parse from "MM/DD/YYYY" to a date object
            return date.strptime(v, "%m/%d/%Y")
        return v