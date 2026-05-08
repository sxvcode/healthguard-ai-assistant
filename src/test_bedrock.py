import os
import boto3
from dotenv import load_dotenv

print("1. Starting script...")
load_dotenv()
print("2. Loaded .env file...")

region = os.getenv('AWS_DEFAULT_REGION')
access_key = os.getenv('AWS_ACCESS_KEY_ID')
secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
session_token = os.getenv('AWS_SESSION_TOKEN')

print(f"-> Target Region: {region}")
print("3. Forcing credentials directly into Boto3...")

# By explicitly declaring them here, we completely disable the IMDS network hang
client = boto3.client(
    service_name='bedrock',
    region_name=region,
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    aws_session_token=session_token
)

try:
    print("4. Reaching out to AWS...")
    response = client.list_foundation_models()
    print("\n✅ SUCCESS! Connected to AWS Bedrock.")
except Exception as e:
    print(f"\n❌ FAILED to connect. Error: {e}")