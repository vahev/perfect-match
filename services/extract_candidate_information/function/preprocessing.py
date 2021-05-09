import textract
import spacy
import os
import re

from spacy.matcher import PhraseMatcher
from . import utils


nlp_en = spacy.load('en_core_web_md')
nlp_es = spacy.load('es_core_news_md')

# Todo - Replace with dynamodb storage
ALL_SKILLS = ['c', 'c++', 'c#', 'objective c', 'visual basic', 'visualbasic', 'vb.net', '.net', 'java', 'javac',
              'java8', 'java10', 'jdk', 'jre', 'javascript', 'js', 'java script', 'es6', 'es7', 'es8', 'es9',
              'ecmascript', 'golang', 'go', 'python', 'py', 'cpython', 'ipython', 'scala', 'julia', 'rust', 'bash',
              'sql', 'node', 'nodejs', 'typescript', 'pascal', 'cobol', 'html', 'html5', 'css', 'css3', 'sass', 'php',
              'php5', 's3', 'simple storage service', 'lambda functions', 'aws', 'availability zone',
              'amazon web services', 'cloud', 'cloud architect', 'api gateway', 'apigateway', 'ecs', 'ers',
              'serverless', 'aws lambda', 'ec2', 'cloud formation', 'cloudformation', 'iaas', 'paas', 'saas',
              'codepipeline', 'elastic beanstalk', 'beanstalk', 'dynamo', 'dynamodb', 'firebase', 'glue',
              'step functions', 'snowflake', 'oracle', 'mongo', 'mongodb', 'cassandra', 'hive', 'parquet', 'hdfs',
              'orc', 'json', 'csv', 'avro', 'redis', 'elastic', 'neo4j', 'mysql', 'sql server', 'oracle db', 'oracledb',
              'postgresql', 'postgre', 'xml', 'spark', 'pandas', 'keras', 'theano', 'sklearn', 'nltk', 'matplotlib',
              'jquery', 'jsp', 'weblogic', 'asp', 'pip', 'pep8', 'pyenv', 'pytest', 'flake8', 'pentaho', 'sap',
              'informatica', 'airflow', 'nifi', 'stitch', 'git', 'github', 'gitlab', 'dba', 'developer',
              'data scientist', 'data engineer', 'software developer', 'fullstack', 'frontend', 'backend', 'sdet',
              'software developer engineer in test', 'architect', 'sap consultor', 'freelancer', 'web developer',
              'technical leader', 'tech lead', 'mobile developer', 'front end', 'back end', 'powerbi', 'tableau',
              'looker', 'kibana', 'grafana', 'agile', 'scrum', 'kanban', 'devops', 'continuous integration',
              'continuous delivery', 'cicd', 'cmm', 'rup']


def extract_candidate_info_from_s3_object(bucket, key):
    print('Reading the binary')
    binary = utils.get_object_from_s3(bucket, key)
    print("Getting the filename")
    filename = _get_filename(key)

    candidate = {'s3_location': os.path.join(bucket, key)}

    print('Extracting text from resume')
    text = _extract_text_from_resume(binary, filename)
    print('Cleaning the text')
    text = _clean_text(text)
    print('Extracting personal information')
    candidate.update(_extract_personal_info(text))
    print('Tokenizing')
    text = _tokenize(text)
    candidate['description'] = text
    print('Skills counting')
    candidate['words_frequency'] = _count_skills(text)

    return candidate


def get_s3_record(event):
    s3_record = event.get('Records')[0].get('s3')
    bucket = s3_record.get('bucket').get('name')
    key = s3_record.get('object').get('key')

    return bucket, key


def _get_filename(s3path):
    return s3path.split('/')[-1]


def _extract_text_from_resume(binary, filename):
    filepath = os.path.join('/tmp', filename)
    with open(filepath, 'wb') as file:
        file.write(binary)

    if filepath.rsplit('.', 1)[-1] == 'txt':
        with open(filepath, 'r') as f:

            return f.read()
    text = str(textract.process(filepath), encoding='utf-8')

    return text


def _clean_text(text):
    special_chars = '*-•/+:><♦〓❑·"|'

    """ Cleaning new lines and tabs"""
    text = text.replace('\n', '. ')
    text = re.sub(r'(\t)+', ' ', text)

    """ Cleaning special chars """
    for char in special_chars:
        text = text.replace(char, ' ')

    """ Cleaning double spaces """
    text = re.sub(r'(\s){2,}', ' ', text)

    """ Cleaning uppercases """
    text = ' '.join([word.title() if word.isupper() else word for word in text.split(' ')])

    return text


def _extract_personal_info(text):
    doc = nlp_es(text)
    personal_info = {
        'candidate': '',
        'email': None,
        'phone': None
    }

    """ Get the name of the candidate from the resume"""
    for entity in doc.ents:
        if entity.label_ in ['PER']:
            personal_info['candidate'] = entity.text
            break

    """ Get the email and the phone of the candidate from the resume"""
    personal_info['phone'] = _get_phone(text)
    for token in doc:
        if _is_email(token.text) and not personal_info.get('email'):
            personal_info['email'] = token.text
            break

    return personal_info


def _tokenize(text):
    tokens = nlp_en(text)
    tokens = [token for token in tokens if not (token.is_stop or token.is_punct or token.is_space)]
    tokens = [token.lemma_.lower().strip() if token.lemma_ != '-PRON-' else token.lower_ for token in tokens]

    return ' '.join(tokens)


def _count_skills(text):
    words_freq = {}
    matcher = PhraseMatcher(nlp_en.vocab)
    matcher.add('SKILLS', None, *[nlp_en(word) for word in ALL_SKILLS])
    doc = nlp_en(text.lower())
    matches = matcher(doc)

    for match_id, start, end in matches:
        span = doc[start:end]
        words_freq[span.text] = words_freq.get(span.text, 0) + 1

    return words_freq


def _is_email(word):
    return True if re.match(r'[^@]+@[^@]+\.[^@]+', word) else False


def _get_phone(text):
    matches = re.match(r'.*\(?([0-9]{3})[ )]?[ .-]?([0-9]{3,4})[ .-]?([0-9]{3,4}).*', text)
    if not matches:
        return None
    return ''.join(matches.groups())