from pyspark.sql import SparkSession
from pyspark.sql.functions import col, regexp_extract, avg, count
from collections import Counter

spark = SparkSession.builder \
    .appName("test") \
    .getOrCreate()
df = spark.read.option("mergeSchema", "true").parquet("hdfs://namenode:9000/silver/aqarmap_sale")

daily_gold = df.groupBy("area", "scrape_date").agg(
    count("*").alias("listing_count"),
    avg("price").alias("avg_price"),
    avg(col("price") / col("size_numeric")).alias("avg_price_per_m2")
)
from pyspark.sql.functions import col, when

df = df.withColumn(
    "is_compound",
    when(col("location_detail").contains("compound"), 1).otherwise(0)
)

df.filter((col("area").isNull()) | (col("area") == "")).count()