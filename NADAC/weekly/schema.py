# Define your schema using Pydantic
from datetime import date
import math
from pydantic import BaseModel, Field, field_validator
from typing import Literal

class NADACWeeklySchema(BaseModel):
    # Forbid extra fields not defined in the schema
    model_config = {
        "extra": "forbid",
    }
    # Define each column. Headers with spaces or special characters are handled using the Field alias.
    NDC_Description: str = Field(alias="NDC Description")
    NDC: str = Field(min_length=11, max_length=11)
    NADAC_Per_Unit: float = Field(alias="NADAC Per Unit")
    Effective_Date: date = Field(alias="Effective Date")
    Pricing_Unit: Literal["ML", "GM", "EA"] = Field(alias="Pricing Unit")
    Pharmacy_Type_Indicator: Literal["C/I"] = Field(alias="Pharmacy Type Indicator")
    OTC: Literal["Y", "N"]
    Explanation_Code: str = Field(alias="Explanation Code")
    Classification_for_Rate_Setting: str = Field(alias="Classification for Rate Setting")
    Corresponding_Generic_Drug_NADAC_Per_Unit: float | None = Field(alias="Corresponding Generic Drug NADAC Per Unit")
    Corresponding_Generic_Drug_Effective_Date: date | None = Field(alias="Corresponding Generic Drug Effective Date")
    As_of_Date: date = Field(alias="As of Date")
    
    # Clean up 'nan' values. Convert to 'None' for optional fields.
    @field_validator("Corresponding_Generic_Drug_NADAC_Per_Unit", "Corresponding_Generic_Drug_Effective_Date", mode="before")
    def nan_to_none(cls, v):
        if isinstance(v, float) and math.isnan(v):
            return None
        return v

    @field_validator("NADAC_Per_Unit", "Corresponding_Generic_Drug_NADAC_Per_Unit")
    def five_decimal_places(cls, v: float) -> float:
        if v is None:
            return v
        if round(v, 5) != v:
            raise ValueError("Field must have 5 decimal places")
        return v
    
    @field_validator('Effective_Date', 'Corresponding_Generic_Drug_Effective_Date', 'As_of_Date', mode='before')
    def parse_custom_date(cls, v):
        if isinstance(v, float) and math.isnan(v):
            return v
        if isinstance(v, str):
            # Parse from "MM/DD/YYYY" to a date object
            return date.strptime(v, "%m/%d/%Y")
        return v
