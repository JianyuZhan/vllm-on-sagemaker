#!/bin/sh

# Trust policy JSON content
TRUST_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "sagemaker.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}'

ROLE_NAME=SageMakerExecutionRoleTest

# Create the role and capture the role ARN
SAGEMAKER_ROLE_ARN=$(aws iam create-role --role-name $ROLE_NAME --assume-role-policy-document "$TRUST_POLICY" --query 'Role.Arn' --output text)

# Attach SageMaker full access policy
aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/AmazonSageMakerFullAccess

# Attach S3 read-only access policy
aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess

# Attach ECR read-only access policy
aws iam attach-role-policy \
    --role-name $ROLE_NAME \
    --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly

echo "$SAGEMAKER_ROLE_ARN"