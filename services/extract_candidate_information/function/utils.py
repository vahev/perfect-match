import boto3
import os


DEPLOY_ENV = os.getenv('ENVIRONMENT')


def get_object_from_s3(bucket, key):
    print(bucket, key)
    client = boto3.client('s3')
    resume = client.get_object(Bucket=bucket, Key=key)

    return resume.get('Body').read()


def list_objects_in_s3(bucket, prefix):
    client = boto3.client('s3')
    objects = client.list_objects_v2(Bucket=bucket, Prefix=prefix).get('Contents')
    return objects
