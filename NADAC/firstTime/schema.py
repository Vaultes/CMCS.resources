# Define your schema using Pydantic
from datetime import datetime
import math
from pydantic import BaseModel, Field, field_validator

class NADACFirstTimeSchema(BaseModel):
    # Forbid extra fields not defined in the schema
    model_config = {
        "extra": "forbid",
    }
    
    Drug_Product: str = Field(alias="Drug Product")
    Brief_Indication_Description: str = Field(alias="Brief Indication/Description")
    Drug_Class: str = Field(alias="Drug Class")
    Package_Size: str = Field(alias="Package Size")
    NCPDP_Billing_Unit_Standard: str = Field(alias="NCPDP Billing Unit Standard")
    NADAC_Rate: float = Field(alias="NADAC Rate")
    Number_of_Active_NDCs_Within_The_RateGroup_That_Are_On_The_Covered_Outpatient_Drug_File: int = Field(alias="Number of Active NDCs Within The RateGroup That Are On The Covered Outpatient Drug File")
    Primary_Reason_Code: str = Field(alias="Primary Reason Code")
    As_of_Date: datetime = Field(alias="As of Date")
    Classification_for_Rate_Setting: str = Field(alias="Classification for Rate Setting")

    @field_validator('As_of_Date', mode='before')
    def parse_custom_date(cls, v: float | str):
        if isinstance(v, float) and math.isnan(v):
            return v
        if isinstance(v, str):
            # Parse from "MM/DD/YYYY" to a datetime object
            return datetime.strptime(v, "%m/%d/%Y")
        return v
