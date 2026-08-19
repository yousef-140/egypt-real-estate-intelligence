import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import regexp_replace, col, udf, current_date, regexp_extract
from pyspark.sql.types import IntegerType, StringType, StructType, StructField
import re
from langdetect import detect, LangDetectException
from datetime import date

HDFS_URI = os.getenv("HDFS_URI", "hdfs://namenode:9000")

today = date.today().isoformat()


def get_spark():
    return SparkSession.builder.appName("AqarmapSilverCleaning").getOrCreate()


def detect_language(text):
    if text is None:
        return None
    try:
        return detect(text)
    except LangDetectException:
        return None


detect_language_udf = udf(detect_language, StringType())


def extract_area_and_detail(location_slug, n=3):
    if location_slug is None:
        return (None, None)

    words = location_slug.split("-")
    if len(words) <= n:
        return (location_slug, None)

    area = "-".join(words[:n])
    detail = "-".join(words[n:])
    return (area, detail)


area_detail_schema = StructType([
    StructField("area", StringType(), True),
    StructField("location_detail", StringType(), True),
])

extract_area_and_detail_udf = udf(extract_area_and_detail, area_detail_schema)


def clean_and_save(bronze_path, silver_path):
    spark = get_spark()
    df = spark.read.json(bronze_path)

    df = df.withColumn("size_numeric", regexp_replace(col("size"), r"[^\d]", "").cast("int"))
    df = df.withColumn("title_language", detect_language_udf(col("title")))
    df = df.withColumn("bedrooms_numeric", col("bedrooms").cast("int"))
    df = df.withColumn("bathrooms_numeric", col("bathrooms").cast("int"))

    df = df.withColumn("location_slug", regexp_extract(col("url"), r"cairo-(.*)/", 1))
    df = df.withColumn("area_detail", extract_area_and_detail_udf(col("location_slug")))
    df = df.withColumn("area", col("area_detail.area"))
    df = df.withColumn("location_detail", col("area_detail.location_detail"))
    df = df.drop("area_detail", "location_slug")

    df_deduped = df.dropDuplicates(["url", "price"])
    df_deduped = df_deduped.withColumn("scrape_date", current_date())

    df_deduped.write.mode("append").partitionBy("scrape_date").parquet(silver_path)


if __name__ == "__main__":
    clean_and_save(f"{HDFS_URI}/bronze/aqarmap_sale_{today}.jsonl", f"{HDFS_URI}/silver/aqarmap_sale")
    clean_and_save(f"{HDFS_URI}/bronze/aqarmap_rent_{today}.jsonl", f"{HDFS_URI}/silver/aqarmap_rent")