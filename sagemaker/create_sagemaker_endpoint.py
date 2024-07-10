import boto3
import argparse

def create_sagemaker_endpoint(region, instance_type, role_arn, image_uri, endpoint_name, model_id):
    sagemaker = boto3.client('sagemaker', region_name=region)

    create_model_response = sagemaker.create_model(
        ModelName=endpoint_name + '-model',
        PrimaryContainer={
            'Image': image_uri,
            'Environment': {
                'API_HOST': '0.0.0.0',
                'API_PORT': '8080',
                'MODEL_ID': model_id,
                'INSTANCE_TYPE': instance_type,
            },
        },
        ExecutionRoleArn=role_arn,
    )

    create_endpoint_config_response = sagemaker.create_endpoint_config(
        EndpointConfigName=endpoint_name + '-config',
        ProductionVariants=[
            {
                'VariantName': 'default',
                'ModelName': endpoint_name + '-model',
                'InstanceType': instance_type,
                'InitialInstanceCount': 1,
            },
        ],
    )

    create_endpoint_response = sagemaker.create_endpoint(
        EndpointName=endpoint_name,
        EndpointConfigName=endpoint_name + '-config',
    )

    print(f"Endpoint {endpoint_name} created. Check on the sagemaker console.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--region', default='us-east-1', help='The region to create the endpoint')
    parser.add_argument('--model_id', required=True, help='The Hugging Face model ID to use')
    parser.add_argument('--instance_type', required=True, help='Instance type for the SageMaker endpoint')
    parser.add_argument('--role_arn', required=True, help='The ARN of the IAM role for SageMaker to access resources')
    parser.add_argument('--image_uri', required=True, help='The URI of the Docker image in ECR')
    parser.add_argument('--endpoint_name', default='vllm-endpoint', help='The name of the endpoint to create')

    args = parser.parse_args()

    create_sagemaker_endpoint(
        region=args.region,
        instance_type=args.instance_type,
        role_arn=args.role_arn,
        image_uri=args.image_uri,
        endpoint_name=args.endpoint_name,
        model_id=args.model_id,
    )
