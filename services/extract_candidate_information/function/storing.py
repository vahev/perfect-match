import decimal
import boto3
import os


def store_candidate(candidate):
    dynamodb = boto3.resource('dynamodb')
    for pos, score in candidate['pos_scores'].items():
        candidate['pos_scores'][pos] = '%.10f' % score

    table = dynamodb.Table('candidates-' + os.getenv('STAGE_ENV'))
    print(candidate['pos_scores'])
    table.put_item(
        Item=candidate
    )
