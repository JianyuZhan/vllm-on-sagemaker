#!/bin/sh

# Default values
DEFAULT_IMG_NAME="vllm-on-sagemaker"
DEFAULT_AWS_REGION="us-east-1"
DEFAULT_TAG="latest"

# Function to display usage
usage() {
    echo "Usage: $0 [options]
Options:
    --img-name    The image name (default: $DEFAULT_IMG_NAME)
    --region      The AWS region (default: $DEFAULT_AWS_REGION)
    --tag         The image tag (default: $DEFAULT_TAG)"
    exit 1
}

# Parse command line arguments
PARSED_OPTIONS=$(getopt -o "" -l img-name:,region:,tag: -- "$@")
if [ $? -ne 0 ]; then
    usage
fi
eval set -- "$PARSED_OPTIONS"

# Initialize variables with default values
IMG_NAME="$DEFAULT_IMG_NAME"
AWS_REGION="$DEFAULT_AWS_REGION"
TAG="$DEFAULT_TAG"

# Set options
while true; do
    case "$1" in
        --img-name)
            IMG_NAME="$2"
            shift 2
            ;;
        --region)
            AWS_REGION="$2"
            shift 2
            ;;
        --tag)
            TAG="$2"
            shift 2
            ;;
        --)
            shift
            break
            ;;
        *)
            usage
            ;;
    esac
done

# Determine domain based on region
if [ "$AWS_REGION" = "cn-north-1" ] || [ "$AWS_REGION" = "cn-northwest-1" ]; then
    DOMAIN="amazonaws.com.cn"
else
    DOMAIN="amazonaws.com"
fi

# Retrieve AWS Account ID
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)

# Get the latest image URI
IMG_URI=$(aws ecr describe-images --repository-name $IMG_NAME \
    --region $AWS_REGION \
    --query "sort_by(imageDetails[?imageTags != null] | [?contains(imageTags, \`${TAG}\`)], &imagePushedAt)[-1].imageTags[0]" \
    --output text |\
awk -v aws_account=$AWS_ACCOUNT \
    -v aws_region=$AWS_REGION \
    -v img_name=$IMG_NAME \
    -v domain=$DOMAIN '{print aws_account ".dkr.ecr." aws_region "." domain "/" img_name ":" $1}')

echo $IMG_URI
