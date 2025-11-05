import boto3
import pandas as pd
from io import StringIO

s3 = boto3.client('s3')
raw_bucket = 'enterprise-raw-data373'
staging_bucket = 'enterprise-staging-data373'

def read_csv_from_s3(bucket, key):
    obj = s3.get_object(Bucket=bucket, Key=key)
    return pd.read_csv(obj['Body'])

def validate_data(df, name):
    print(f"Validating {name}...")
    print("Null values:\n", df.isnull().sum())
    print("Duplicates:", df.duplicated().sum())
    return df.drop_duplicates()

def write_csv_to_s3(df, bucket, key):
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    s3.put_object(Bucket=bucket, Key=key, Body=csv_buffer.getvalue())

def main():
    files = {
        'customers': 'customers/customers.csv',
        'orders': 'orders/orders.csv',
        'products': 'products/products.csv'
    }
    for name, key in files.items():
        df = read_csv_from_s3(raw_bucket, key)
        clean_df = validate_data(df, name)
        staging_key = f"{name}/{name}_clean.csv"
        write_csv_to_s3(clean_df, staging_bucket, staging_key)
        print(f"{name} cleaned and uploaded to staging bucket.")

if __name__ == "__main__":
    main()
