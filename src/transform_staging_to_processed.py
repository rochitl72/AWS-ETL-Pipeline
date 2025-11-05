import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.dynamicframe import DynamicFrame
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import col, round, year, to_date

glueContext = GlueContext(SparkContext.getOrCreate())
spark = glueContext.spark_session
job = Job(glueContext)

# ===============================
# 1️⃣ READ FROM S3 STAGING BUCKETS
# ===============================
customers_path = "s3://enterprise-staging-data373/customers/"
orders_path = "s3://enterprise-staging-data373/orders/"
products_path = "s3://enterprise-staging-data373/products/"

customers_dyf = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={"paths": [customers_path], "recurse": True},
    format="csv",
    format_options={"withHeader": True}
)

orders_dyf = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={"paths": [orders_path], "recurse": True},
    format="csv",
    format_options={"withHeader": True}
)

products_dyf = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={"paths": [products_path], "recurse": True},
    format="csv",
    format_options={"withHeader": True}
)

# Convert to DataFrames for transformation
customers_df = customers_dyf.toDF()
orders_df = orders_dyf.toDF()
products_df = products_dyf.toDF()

# ===============================
# 2️⃣ CLEAN AND STANDARDIZE COLUMNS
# ===============================
# Customers
customers_df = customers_df.selectExpr(
    "cast(customer_id as int) customer_id",
    "customer_name",
    "region"
)

# Orders
orders_df = orders_df.selectExpr(
    "cast(order_id as int) order_id",
    "cast(customer_id as int) customer_id",
    "cast(product_id as int) product_id",
    "cast(ordered_quantity as int) ordered_quantity",
    "cast(order_date as string) order_date"
)

# Products
products_df = products_df.selectExpr(
    "cast(product_id as int) product_id",
    "product_description",
    "cast(standard_price as double) standard_price"
)

# ===============================
# 3️⃣ JOIN TABLES
# ===============================
joined_df = (
    orders_df
    .join(customers_df, "customer_id", "left")
    .join(products_df, "product_id", "left")
)

# Add calculated columns
joined_df = (
    joined_df
    .withColumn("extended_price", round(col("ordered_quantity") * col("standard_price"), 2))
    .withColumn("order_year", year(to_date(col("order_date"))))
)

# ===============================
# 4️⃣ CONVERT BACK TO DYNAMIC FRAME
# ===============================
joined_dyf = DynamicFrame.fromDF(joined_df, glueContext, "joined_dyf")

# ===============================
# 5️⃣ WRITE OUTPUT TO S3 (PROCESSED)
# ===============================
output_path = "s3://enterprise-processed-data373/customer_orders_analytics/"

glueContext.write_dynamic_frame.from_options(
    frame=joined_dyf,
    connection_type="s3",
    connection_options={"path": output_path, "partitionKeys": ["order_year"]},
    format="parquet"
)

job.commit()
