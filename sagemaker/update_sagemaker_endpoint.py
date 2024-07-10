import argparse
import boto3
from time import sleep
from datetime import datetime

def get_next_version_name(sagemaker, base_name, date, prefix):
    # 根据前缀确定是模型还是端点配置
    existing_names = []
    if prefix == 'model':
        existing_names = [model['ModelName'] for model in sagemaker.list_models()['Models']]
    elif prefix == 'config':
        existing_names = [config['EndpointConfigName'] for config in sagemaker.list_endpoint_configs()['EndpointConfigs']]
    
    # 筛选出符合基础名称和日期的名称
    version_nums = []
    for name in existing_names:
        if name.startswith(f"{base_name}-{date}v"):
            version_num = name.split('v')[-1]
            if version_num.isdigit():
                version_nums.append(int(version_num))
    
    # 确定下一个版本号
    if version_nums:
        next_version = max(version_nums) + 1
    else:
        next_version = 1
    
    return f"{base_name}-{date}v{next_version}"

def main(args):
    sagemaker = boto3.client('sagemaker', region_name=args.region)
    date = datetime.now().strftime('%Y%m%d')

    # the new model name and endpoint config name
    model_name = get_next_version_name(sagemaker, args.endpoint_name, date, 'model')
    endpoint_config_name = get_next_version_name(sagemaker, args.endpoint_name, date, 'config')

    # Create new model
    create_model_response = sagemaker.create_model(
        ModelName=model_name,
        PrimaryContainer={
            'Image': args.image,
            'Environment': {
                'API_HOST': '0.0.0.0',
                'API_PORT': '8080',
                'MODEL_ID': args.model_id,
                'INSTANCE_TYPE': args.instance_type,
            }
        },
        ExecutionRoleArn=args.role_arn
    )
    print(f"Using image: {args.image}")
    print(f"Using model: {args.model_id}")
    print(f"Created model: {create_model_response['ModelArn']}")

    # Create new endpoing config
    create_endpoint_config_response = sagemaker.create_endpoint_config(
        EndpointConfigName=endpoint_config_name,
        ProductionVariants=[
            {
                'VariantName': 'variant-1',
                'ModelName': model_name,
                'InstanceType': args.instance_type,
                'InitialInstanceCount': 1
            },
        ],
    )
    print(f"Using instance type: {args.instance_type}")
    print(f"Created endpoint config: {create_endpoint_config_response['EndpointConfigArn']}")

    # Upate the endpoint!
    update_endpoint_response = sagemaker.update_endpoint(
        EndpointName=args.endpoint_name,
        EndpointConfigName=endpoint_config_name
    )
    print(f"Updating endpoint: {update_endpoint_response['EndpointArn']}")

    # 检查更新状态
    while True:
        response = sagemaker.describe_endpoint(EndpointName=args.endpoint_name)
        status = response['EndpointStatus']
        print(f"Endpoint status: {status}")
        if status in ['InService', 'Failed']:
            break
        sleep(10)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Update SageMaker endpoint.')
    parser.add_argument('--region', default='us-east-1', help='The region to create the endpoint')
    parser.add_argument('--endpoint_name', type=str, required=True, help='Name of the SageMaker endpoint')
    parser.add_argument('--role_arn', type=str, required=True, help='ARN of the Sagemaker execution role')
    parser.add_argument('--image', type=str, required=True, help='URI of the Docker image')
    parser.add_argument('--model_id', type=str, help='Huggingface ID for the new model')
    parser.add_argument('--instance_type', type=str, required=True, help='Type of instance to deploy the model')

    args = parser.parse_args()
    main(args)