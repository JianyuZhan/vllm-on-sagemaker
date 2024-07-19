# SageMaker Endpoint for vLLM

You can use the [LMI](https://docs.djl.ai/docs/serving/serving/docs/lmi/index.html) to easily run vLLM on Amazon SageMaker. However, the version of vLLM supported by LMI lags several versions behind the latest community version. If you want to run the latest version, try this repo!

## Prerequisites

Make sure you have the following tools installed:
- AWS CLI (and run `aws configure`)
- Docker
- Python 3

## Usage

### 1. Set Environment Variables

Start by setting up some environment variables. Adjust them as needed:

```sh
export REGION='us-east-1' # change as needed
export IMG_NAME='vllm-on-sagemaker' # change as needed
export IMG_TAG='latest' # change as needed
export SAGEMAKER_ENDPOINT_NAME='vllm-on-sagemaker' # change as needed
```

### 2. Build and Push Docker Image

Build the Docker image that will be used to run the SageMaker Endpoint serving container. After building, the image will be pushed to AWS ECR. The container implements `/ping` and `/invocations` APIs, as required by SageMaker Endpoints.

```sh
sagemaker/build_and_push_image.sh --region "$REGION" --image-name "$IMG_NAME" --tag "$IMG_TAG"
```

### 3. Get the Image URI

After the image is built and pushed, retrieve the image URI:

```sh
export IMG_URI=$(sagemaker/get_ecr_image_uri.sh --region "$REGION" --img-name "$IMG_NAME" --tag "$IMG_TAG")
echo $IMG_URI
```

### 4. Create a SageMaker Execution Role

Create a SageMaker execution role to allow the endpoint to run properly:

```sh
export SM_ROLE=$(sagemaker/create_sagemaker_execute_role.sh)
echo $SM_ROLE
```

### 5. Create the SageMaker Endpoint

Now, create the SageMaker Endpoint. Choose the appropriate Hugging Face model ID and instance type:

```sh
python3 sagemaker/create_sagemaker_endpoint.py \
    --region "$REGION" \
    --model_id "deepseek-ai/deepseek-llm-7b-chat" \
    --instance_type ml.g5.4xlarge \
    --role_arn $SM_ROLE \
    --image_uri $IMG_URI \
    --endpoint_name $SAGEMAKER_ENDPOINT_NAME
```

### 6. Check the Endpoint

Go to the AWS console -> SageMaker -> Inference -> Endpoints. You should see the endpoint being created. Wait until the creation process is complete.

### 7. Send Requests to the Endpoint

Once the endpoint is created and in 'InService' status, you can start sending requests to it.

You can use the SageMaker `/invocations` API to call the endpoint; it is compatible with the OpenAI chat completion API. Check the `sagemaker/test_endpoint.py` for example requests.
