from pandantic import Pandantic
import pandas

# Need to make this a parameter/flag that can be passed in.
log = False

# Validation logic using pandantic
def validateDataFrame(df: pandas.DataFrame, targetSchema):
    validator = Pandantic(schema=targetSchema)

    if log:
        valid = validator.validate(df, errors='log')
        diff = pandas.concat([df, valid]).drop_duplicates(keep=False)
        print(diff)

    # Validate the DataFrame against the schema
    try:
        validator.validate(df, errors='raise')
    except ValueError as e:
        print(f"Validation error: {e}")
        exit(1)
    pass