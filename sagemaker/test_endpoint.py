import argparse
import sys
import io
import json
import boto3
import botocore


def process_response(resp_body):
    assert isinstance(resp_body, botocore.response.StreamingBody)

    buffer = ''
    for line in resp_body.iter_lines():
        if not line:
            continue

        data_str = line.decode('utf-8')
        # strip the data: prefix
        if data_str.startswith("data: "):
            data_str = data_str[len("data: "):]

        try:
            buffer += data_str
            data = json.loads(buffer.strip())
        except json.JSONDecodeError as e:
            continue
        else:
            buffer = ''

        for choice in data['choices']:
            if 'message' in choice:
                # parameter 'stream = False' in req
                print(choice['message']['content'])
            else:
                # parameter 'stream = True' in req
                if 'content' in choice['delta']:
                    print(choice['delta']['content'], end="")
                    sys.stdout.flush()
    print('')

def process_streaming_body(streaming_body):
    assert isinstance(streaming_body, botocore.eventstream.EventStream)

    buffer = ''
    for event in streaming_body:
        data_str = event["PayloadPart"]["Bytes"].decode('utf-8')
        # strip the data: prefix
        if data_str.startswith("data: "):
            data_str = data_str[len("data: "):]

        try:
            buffer += data_str
            data = json.loads(buffer.strip())
        except json.JSONDecodeError as e:
            continue
        else:
            buffer = ''

        for choice in data['choices']:
            if 'content' in choice['delta']:
                print(choice['delta']['content'], end='')
                sys.stdout.flush() # Don‘t buffer, print immediately...
    
    print('') # EOS


parser = argparse.ArgumentParser(description='Send a request to the SageMaker endpoint for inference.')
parser.add_argument('--region', type=str, default='us-east-1', help='The region of the SageMaker endpoint')
parser.add_argument('--endpoint_name', type=str, required=True, help='The SageMaker endpoint')
args = parser.parse_args()


# Create SageMaker runtime client
client = boto3.client("runtime.sagemaker", region_name=args.region)


# 
# Demo: Non-streaming mode
#
# parameters are compatible with OpenAI API format: 
# https://platform.openai.com/docs/api-reference/introduction
# with extra ones supported by vLLM, see vLLM Docs.
#
# Note! The streaming behavior is actually controlled by the 'stream=True' parameter
# inside the vLLM, but since you use invoke_endpoint,
# even if you pass 'stream=True', you still won't get the real streaming response.
payload = {
    # NOTE! The 'model' parameter is mandated by OpenAI API interface,
    # but it doesn't mean we can choose the model on the fly, the model is set
    # when creating the Sagemaker Endpoiont.
    "model": "deepseek-ai/deepseek-llm-7b-chat",
    # "stream": True,
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": "What is Deep Learning?"
        }
    ],
    "max_tokens": 1024
}
print(f"\n\n=========== Testing non-streaming API ===========")
sys.stdout.flush()
response = client.invoke_endpoint(
    EndpointName=args.endpoint_name,
    Body=json.dumps(payload),
    ContentType="application/json",
)
print(type(response['Body'])) # botocore.response.StreamingBody
process_response(response['Body'])


# 
# Demo: streaming mode
#
# parameters are compatible with OpenAI API format: 
# https://platform.openai.com/docs/api-reference/introduction
# with extra ones supported by vLLM, see vLLM Docs.
# 
# Note! The streaming behavior is actually controlled by the 'stream=True' parameter
# inside the vLLM, but if you use invoke_endpoint, instead of invoke_endpoint_with_response_stream,
# even if you pass 'stream=True', you still won't get the real streaming response.
# 
spayload = {
    # NOTE! The 'model' parameter is mandated by OpenAI API interface,
    # but it doesn't mean we can choose the model on the fly, the model is set
    # when creating the Sagemaker Endpoiont.
    "model": "deepseek-ai/deepseek-llm-7b-chat",
    "stream": True,
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": "What is Deep Learning?"
        }
    ],
    "max_tokens": 1024
}
assert 'stream' in spayload and spayload['stream'], "stream=True must be set when using invoke_endpoint_with_response_stream "
print(f"\n\n=========== Testing streaming API ===========")
sys.stdout.flush()
stream_response = client.invoke_endpoint_with_response_stream(
    EndpointName=args.endpoint_name,
    Body=json.dumps(spayload),
    ContentType="application/json",
)
print(type(stream_response['Body'])) # botocore.eventstream.EventStream
process_streaming_body(stream_response['Body'])