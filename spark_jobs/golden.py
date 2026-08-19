import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import regexp_replace, col, udf, current_date, regexp_extract, avg, count, when, lit, coalesce, round as spark_round
from pyspark.sql.types import IntegerType, StringType, StructType, StructField
import re


HDFS_URI = os.getenv("HDFS_URI", "hdfs://namenode:9000")

spark = SparkSession.builder \
    .appName("golden") \
    .getOrCreate()

df = spark.read.option("mergeSchema", "true").parquet(f"{HDFS_URI}/silver/aqarmap_sale")
df = df.withColumn("area", when(col("area").isNull() | (col("area") == ""), "unknown").otherwise(col("area")))

df = df.withColumn(
    "size_bin",
    when(col("size_numeric") < 100, "small")
    .when(col("size_numeric") < 150, "medium")
    .when(col("size_numeric") < 200, "large")
    .when(col("size_numeric") < 300, "xlarge")
    .otherwise("huge")
)

size_bin_avgs = df.groupBy("size_bin").agg(
    avg("bedrooms_numeric").alias("avg_bedrooms_for_bin"),
    avg("bathrooms_numeric").alias("avg_bathrooms_for_bin")
)
df = df.join(size_bin_avgs, on="size_bin", how="left")

df = df.withColumn(
    "bedrooms_is_predicted",
    when(col("bedrooms_numeric").isNull(), True).otherwise(False)
)
df = df.withColumn(
    "bathrooms_is_predicted",
    when(col("bathrooms_numeric").isNull(), True).otherwise(False)
)

df = df.withColumn(
    "bedrooms_numeric",
    coalesce(col("bedrooms_numeric"), spark_round(col("avg_bedrooms_for_bin")))
)
df = df.withColumn(
    "bathrooms_numeric",
    coalesce(col("bathrooms_numeric"), spark_round(col("avg_bathrooms_for_bin")))
)
df.filter(col("bedrooms_is_predicted") == True).select("size_bin", "bedrooms_numeric", "bathrooms_numeric", "bedrooms_is_predicted").show(10)
sale_gold = df.groupBy("area").agg(
    count("*").alias("listing_count"),
    avg("price").alias("avg_price"),
    avg(col("price") / col("size_numeric")).alias("avg_price_per_m2")
)
#sale_gold.orderBy(col("listing_count").desc()).show(30, truncate=False)


rent_df = spark.read.option("mergeSchema", "true").parquet("hdfs://namenode:9000/silver/aqarmap_rent")
rent_gold = rent_df.groupBy("area").agg(
    count("*").alias("rent_listing_count"),
    avg("price").alias("avg_monthly_rent")
)
#rent_gold.orderBy(col("rent_listing_count").desc()).show(30, truncate=False)

combined = sale_gold.join(rent_gold, on="area", how="inner")
combined = combined.withColumn(
    "rental_yield_percent",
    (col("avg_monthly_rent") * 12 / col("avg_price")) * 100
)

sale_gold.write.mode("overwrite").parquet(f"{HDFS_URI}/gold/sale_gold")
combined.write.mode("overwrite").parquet(f"{HDFS_URI}/gold/rental_yield")
sale_gold.coalesce(1).write.mode("overwrite").option("header", "true").csv(f"{HDFS_URI}/exports/sale_gold_csv")
combined.coalesce(1).write.mode("overwrite").option("header", "true").csv(f"{HDFS_URI}/exports/rental_yield_csv")