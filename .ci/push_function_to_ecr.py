import argparse
import base64
import docker
import boto3
import sys
import os


def main():

    app_namespace = 'augurio'
    services_dir = '../services'
    function_name = args.function
    existing_functions = [obj for obj in os.listdir(services_dir) if os.path.isdir(os.path.join(services_dir, obj))]
    repository_name = os.path.join(app_namespace, function_name)
    function_path = os.path.join(services_dir, function_name)

    if function_name not in existing_functions:
        print('The provided function is not defined:')
        print(f'Existing functions: {existing_functions}')
        sys.exit(1)

    print('Setting up the sessions...')
    ecr_client = boto3.client('ecr')
    auth = ecr_client.get_authorization_token().get('authorizationData')[0]
    username, password, registry = get_credentials_from_auth_token(auth)
    docker_client = docker.from_env()
    login_status = docker_client.login(username, password, registry=registry, reauth=True)
    if login_status.get('Status') not in 'Login Succeeded':
        print(f'Docker was unable to login into {registry}')
        sys.exit(1)

    print(f'Building docker image for {function_name}...')
    docker_client.images.build(path=function_path, tag=os.path.join(registry, repository_name), rm=True)

    print('Preparing ECR...')
    existing_ecr_repos = [repo.get('repositoryName') for repo in
                          ecr_client.describe_repositories().get('repositories')]

    if repository_name not in existing_ecr_repos:
        print('Creating ECR repository...')
        ecr_client.create_repository(repositoryName=repository_name)

    print(f'Deploying the docker image for {repository_name} to ECR...')

    for line in docker_client.images.push(repository=os.path.join(registry, repository_name),
                                          stream=True, decode=True):
        print(line)
        if line.get('errorDetail'):
            sys.exit(1)

    for line in docker_client.images.push(repository=os.path.join(registry, repository_name),
                                          tag='v1', stream=True, decode=True):
        print(line)
        if line.get('errorDetail'):
            sys.exit(1)

    print('Image pushed successfully into ECR registry')


def get_credentials_from_auth_token(token):
    token_decoded = base64.b64decode(token.get('authorizationToken')).decode()
    endpoint = token.get('proxyEndpoint').replace('https://', '')
    username = token_decoded.split(':')[0]
    password = token_decoded.split(':')[-1]

    return username, password, endpoint


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Copies a source S3 object into a target S3 object'
    )
    parser.add_argument('function', type=str, help='the name of the Lambda function to deploy to ECR')
    parser.add_argument('--region', type=str, help='the aws region where you want to deploy the docker image')
    parser.add_argument('--registry', type=str, help='the aws ECS registry to deploy the image into')
    args = parser.parse_args()
    main()
