# PyTest Script: tests/test_pii_masking.py
# Purpose: Unit testing the PII Masking Engine logic

import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType
from governance_automation.PII_Masking_Engine import PIIMasker

@pytest.fixture(scope="session")
def spark():
    return SparkSession.builder.master("local[1]").appName("MediFlowTesting").getOrCreate()

def test_mask_email(spark):
    # 1. Create sample data
    data = [("arjun.patel@gmail.com",), ("priya@mrhs.in",)]
    schema = StructType([StructField("email", StringType(), True)])
    df = spark.createDataFrame(data, schema)
    
    # 2. Apply masking
    masked_df = PIIMasker.mask_email(df, "email")
    results = masked_df.collect()
    
    # 3. Assertions
    # Pattern: a***l@gmail.com
    assert results[0]["email"] == "a***l@gmail.com"
    assert results[1]["email"] == "p***a@mrhs.in"

def test_mask_phone(spark):
    data = [("9876543210",)]
    schema = StructType([StructField("phone_number", StringType(), True)])
    df = spark.createDataFrame(data, schema)
    
    masked_df = PIIMasker.mask_phone(df, "phone_number")
    result = masked_df.collect()[0]["phone_number"]
    
    assert result == "XXXXXX-3210"
