import argparse
import boto3
import time
import sys


def main():
    stage = args.stage
    stack_name = '-'.join([args.stack_name, stage])
    params = [{'ParameterKey': variable.split(',')[0], 'ParameterValue': variable.split(',')[1]} for variable in args.params.split(';')] if args.params else []
    with open(args.template, 'r') as file:
        template = file.read()

    client = boto3.client('cloudformation')
    all_stacks = {stack['StackName'] for stack in client.list_stacks()['StackSummaries']}
    deleted_stacks = {stack['StackName'] for stack in client.list_stacks(
        StackStatusFilter=['DELETE_COMPLETE'])['StackSummaries']}
    existing_stacks = all_stacks - deleted_stacks
    print(stack_name, params)
    print(all_stacks)
    print(deleted_stacks)
    print(existing_stacks)
    if stack_name not in existing_stacks:
        stack_info = client.create_stack(StackName=stack_name,
                                         TemplateBody=template,
                                         Parameters=params,
                                         DisableRollback=True,
                                         Capabilities=['CAPABILITY_AUTO_EXPAND',
                                                       'CAPABILITY_NAMED_IAM',
                                                       'CAPABILITY_IAM'])
    else:
        stack_info = client.update_stack(StackName=stack_name,
                                         TemplateBody=template,
                                         Parameters=params)

    finished_status = ['CREATE_COMPLETE', 'CREATE_FAILED', 'ROLLBACK_COMPLETE', 'ROLLBACK_FAILED']
    stack_status = ''
    stack_process_finished = False
    start_time = time.time()
    timeout = 1000

    while not stack_process_finished or (time.time() - start_time) >= timeout:
        time.sleep(5)
        print(f'Creating Stack... {time.time() - start_time}s elapsed', end='\x1b[1K\r')
        stack_description = client.describe_stacks(StackName=stack_name)['Stacks'][0]
        stack_status = stack_description['StackStatus']
        if stack_status in finished_status:
            stack_process_finished = True

    if stack_status not in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
        print(f'Stack creation failed due to {stack_description["StackStatusReason"]}')
        # Todo - change this ASAP
        print('We should rollback here, but for now we will delete if not successful deployment')
        print('Deleting it for the moment')
        client.delete_stack(StackName=stack_name)
        sys.exit(1)

    print('Stack creation successful')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Deploys the AWS infrastructure needed to deploy the application'
    )
    parser.add_argument('stack_name', type=str, help='the name of the cloudFormation stack to deploy')
    parser.add_argument('stage', type=str, help='the stage environment of the stack/app')
    parser.add_argument('template', type=str, help='The cloudformation stack template to deploy')
    parser.add_argument('--params', type=str,
                        help='additional parameters to pass to the cloudFormation template in the form "Param1Key,Param1Value;Param2Key,param2Value"')
    args = parser.parse_args()
    main()
