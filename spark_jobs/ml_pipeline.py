import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, lit, when, coalesce, regexp_replace, round as spark_round, round as spark_round2, regexp_extract
from pyspark.ml.feature import StringIndexer, VectorAssembler, OneHotEncoder
from pyspark.ml.regression import RandomForestRegressor
from pyspark.ml.evaluation import RegressionEvaluator

HDFS_URI = os.getenv("HDFS_URI", "hdfs://namenode:9000")

spark = SparkSession.builder \
    .appName("ml_pipeline") \
    .getOrCreate()

df = spark.read.option("mergeSchema", "true").parquet(f"{HDFS_URI}/silver/aqarmap_sale")

df = df.withColumn("price", regexp_replace(col("price"), "[^0-9.]", "").cast("double"))
df = df.filter(col("price").isNotNull())
df = df.filter(col("price") > 200000)
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

df = df.withColumn(
    "is_compound",
    when(col("location_detail").contains("compound"), 1).otherwise(0)
)

df = df.withColumn(
    "compound_raw",
    when(col("location_detail").contains("compound"),
         regexp_extract(col("location_detail"), r"compounds?-(.+)", 1))
    .otherwise(lit(None))
)
df = df.withColumn(
    "compound_raw",
    when(col("compound_raw") == "", lit(None)).otherwise(col("compound_raw"))
)

compound_counts = df.groupBy("compound_raw").count()
frequent_compounds = compound_counts.filter(col("count") >= 10).select("compound_raw")
frequent_list = [row["compound_raw"] for row in frequent_compounds.collect()]
df = df.withColumn(
    "compound_final",
    when(col("compound_raw").isNull(), "no_compound")
    .when(col("compound_raw").isin(frequent_list), col("compound_raw"))
    .otherwise("other_compound")
)

df = df.withColumn("listing_id", regexp_extract(col("url"), r"listing/(\d+)-", 1))
df = df.dropDuplicates(["listing_id", "price"])

indexer = StringIndexer(inputCol="area", outputCol="area_index", handleInvalid="keep")
indexer_model = indexer.fit(df)
df_indexed = indexer_model.transform(df)

encoder = OneHotEncoder(inputCol="area_index", outputCol="area_encoded")
encoder_model = encoder.fit(df_indexed)
df_indexed2 = encoder_model.transform(df_indexed)

compound_indexer = StringIndexer(inputCol="compound_final", outputCol="compound_index", handleInvalid="keep")
compound_indexer_model = compound_indexer.fit(df_indexed2)
df_indexed3 = compound_indexer_model.transform(df_indexed2)

compound_encoder = OneHotEncoder(inputCol="compound_index", outputCol="compound_encoded")
compound_encoder_model = compound_encoder.fit(df_indexed3)
df_encoded = compound_encoder_model.transform(df_indexed3)

assembler = VectorAssembler(
    inputCols=["size_numeric", "bedrooms_numeric", "bathrooms_numeric", "area_encoded", "is_compound", "compound_encoded"],
    outputCol="features"
)
df_final = assembler.transform(df_encoded)

df_final.select("features", "price").show(10, truncate=False)

training_data, test_data = df_final.randomSplit([0.8, 0.2], seed=42)
print(f"Training data count: {training_data.count()}, Test data count: {test_data.count()}")

rf = RandomForestRegressor(
    featuresCol="features",
    labelCol="price",
    seed=42,
    numTrees=50,
    maxDepth=15
)
model = rf.fit(training_data)

predictions = model.transform(test_data)

evaluator = RegressionEvaluator(labelCol="price", predictionCol="prediction", metricName="rmse")
rmse = evaluator.evaluate(predictions)
print(f"RMSE: {rmse}")

evaluator_r2 = RegressionEvaluator(labelCol="price", predictionCol="prediction", metricName="r2")
r2 = evaluator_r2.evaluate(predictions)
print(f"R2: {r2}")

all_predictions = model.transform(df_final)

all_predictions = all_predictions.withColumn(
    "fair_value_score",
    spark_round2(((col("price") - col("prediction")) / col("prediction")) * 100, 2)
)

all_predictions.select("url", "area", "price", "prediction", "fair_value_score") \
    .orderBy("fair_value_score") \
    .show(15, truncate=False)

all_predictions.select("url", "area", "price", "prediction", "fair_value_score") \
    .coalesce(1).write.mode("overwrite").option("header", "true").csv(f"{HDFS_URI}/exports/fair_value_csv")