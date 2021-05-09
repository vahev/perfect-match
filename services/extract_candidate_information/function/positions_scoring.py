import pandas as pd
import io

from . import utils

S3_BUCKET = 'enroute-dev-dl-augurio'
MODELS_PREFIX = 'models'


def get_positions_scores(candidate):
    models = _load_available_models()
    models_scores = {}
    for model_name, model in models.items():
        resume_description = candidate.get('description')
        score = model.predict_proba([resume_description])[0][-1]
        models_scores[model_name] = score
        print(f'{model_name} scored : {score}')

    return models_scores


def _load_available_models():
    models = {}
    bucket = S3_BUCKET
    objects = utils.list_objects_in_s3(S3_BUCKET, MODELS_PREFIX)
    print('Loading the models')

    for obj in objects:
        key = obj.get('Key')
        if key.split('.')[-1] not in 'pickle':
            continue

        model_name = _get_model_name(key)
        model = utils.get_object_from_s3(bucket, key)
        models[model_name] = pd.read_pickle(io.BytesIO(model))

    return models


def _get_model_name(key):
    return key.split('/')[-1].split('.')[0]
