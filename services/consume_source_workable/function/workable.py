import requests
import hashlib
import boto3
import time
import io
import os


class Workable:

    Success_codes = [200, 201, 202, 204]

    def __init__(self, account, apikey):
        self.account = account.lower()
        self.apikey = str(apikey)
        self.api_base = 'https://{}.workable.com/spi/v3/'.format(account)
        self.headers = {
            'Content-Type': 'application/json',
            'authorization': 'Bearer {}'.format(self.apikey)
        }

    @staticmethod
    def download_candidate_resume(resume_url):
        response = requests.get(resume_url)
        extension = '.doc'
        bucket = os.getenv('S3_BUCKET')
        prefix = 'raw-resumes'
        if ('word/document.xml' in response.text[-900:-100]) or ('PK' in response.text[:5]):
            extension = '.docx'
        if 'PDF' in response.text[:10]:
            extension = '.pdf'
        filename = hashlib.md5(response.text.encode("utf8")).hexdigest() + extension
        print(f'Uploading {filename}')
        Workable.save_file_in_s3(bucket, os.path.join(prefix, filename), response.content)

    @staticmethod
    def save_file_in_s3(bucket, key, obj):
        client = boto3.client('s3')
        client.upload_fileobj(io.BytesIO(obj), bucket, key)
        print('resume uploaded successfully')

    def get_candidate_detail(self, candidate_id):
        response = requests.get(self.api_base + 'candidates/{}'.format(candidate_id), headers=self.headers)
        self._check_status(response)
        return response.json()['candidate']

    def download_candidates_resumes(self, candidates):
        counter = 0
        print('downloading candidates resumes')
        for candidate in candidates:
            detail = self.get_candidate_detail(candidate['id'])
            if not detail['resume_url']:
                print('Not resume provided for {}'.format(detail['name']))
                continue
            # Todo - evaluate extracting the name from here and create a composed id to be processed downstream
            self.download_candidate_resume(detail['resume_url'])
            counter += 1
            print('Resumes uploaded: ', counter)
            if counter % 7 == 0:
                time.sleep(1)

    def get_candidates(self, limit=10, stage=None, updated_after=None):
        params = {'limit': limit}
        candidates = []
        endpoint = self.api_base + 'candidates/'

        if stage:
            params['stage'] = stage
        if updated_after:
            params['updated_after'] = updated_after

        if limit <= 100:
            response = requests.get(endpoint, headers=self.headers, params=params)
            self._check_status(response)
            candidates = candidates + response.json()['candidates']
        else:
            params['limit'] = 100
            next_url = None
            while limit > 0:
                if next_url:
                    endpoint = next_url
                response = requests.get(endpoint, headers=self.headers, params=params)
                self._check_status(response)
                candidates = candidates + response.json()['candidates']
                next_url = response.json()['paging'].get('next')
                limit = limit - 100
                if limit < 100:
                    params['limit'] = limit

        print('{} candidates retrieved'.format(len(candidates)))
        return candidates

    def _check_status(self, response):
        print(response.status_code)
        if response.status_code >= 500:
            raise Exception('Internal server Error {}'.format(response.status_code))
        elif response.status_code not in self.Success_codes:
            raise Exception('Status code {}'.format(response.status_code))
