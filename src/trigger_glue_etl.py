import os
import json
import boto3
from botocore.exceptions import ClientError

GLUE_JOB_NAME = os.getenv("GLUE_JOB_NAME", "transform_staging_to_processed")
glue = boto3.client("glue")

def lambda_handler(event, context):
    try:
        resp = glue.start_job_run(JobName=GLUE_JOB_NAME)
        job_run_id = resp["JobRunId"]
        print({"message": "Glue job started", "job_name": GLUE_JOB_NAME, "job_run_id": job_run_id})

        # (optional) return the run id to upstream callers
        return {"statusCode": 200, "body": json.dumps({"job_run_id": job_run_id})}

    except ClientError as e:
        print({"error": str(e), "job_name": GLUE_JOB_NAME})
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
