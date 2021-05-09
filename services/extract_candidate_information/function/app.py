import json

from . import preprocessing
from . import positions_scoring
from . import storing


def handler(event, context):
    # Todo- Get rid of this before commit
    print('Reading the resume from S3')
    _ = context
    bucket, key = preprocessing.get_s3_record(event)
    print(bucket, key)
    candidate = preprocessing.extract_candidate_info_from_s3_object(bucket, key)
    candidate['pos_scores'] = positions_scoring.get_positions_scores(candidate)
    print(f'Information for [{candidate["candidate"]}] extracted successfully')
    candidate['id'] = candidate['s3_location'].split('/')[-1].split('.')[0]
    print('Storing information in DB...')
    storing.store_candidate(candidate)
    print(f'Candidate {candidate["candidate"]} store successfully')

    return {
        'statusCode': 200,
        'body': json.dumps(candidate)
    }
