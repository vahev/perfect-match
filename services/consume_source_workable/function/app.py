import boto3
import json

from datetime import datetime, timedelta
from workable import Workable


def handler(event, context):
    _ = context
    print(event)
    date_format = '%Y-%m-%dT%H:%M:%SZ'
    process_from_date = datetime.strptime(event['time'], date_format) - timedelta(days=1)
    ssm_client = boto3.client('ssm')
    token = ssm_client.get_parameter(Name='/augurio/WORKABLE_TOKEN')['Parameter']['Value']
    print('Instantiating Workable object')
    print(token)
    workable_client = Workable('enroute', token)
    print('retrieving candidates...')
    candidates = workable_client.get_candidates(limit=1000, updated_after=process_from_date.strftime(date_format))
    print(f'Candidates retrieved: {len(candidates)}')
    workable_client.download_candidates_resumes(candidates)

    return {
        'statusCode': 200,
        'body': json.dumps({'candidates': candidates})
    }


if __name__ == '__main__':
    handler({'time': '2016-01-01T03:39:46Z'}, None)
