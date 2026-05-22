from pandantic import Pandantic
import pandas

# Validation logic using pandantic
def validateDataFrame(df: pandas.DataFrame, targetSchema):
    validator = Pandantic(schema=targetSchema)

    # Validate the DataFrame against the schema
    try:
        validator.validate(df, errors='raise')
    except ValueError as e:
        print(f"Validation error: {e}")
        exit(1)
    pass