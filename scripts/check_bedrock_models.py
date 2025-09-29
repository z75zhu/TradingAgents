#!/usr/bin/env python3
"""
Check available models in AWS Bedrock.
"""

import boto3
from botocore.exceptions import ClientError

def list_available_models():
    """List all available foundation models in Bedrock."""
    try:
        # Create Bedrock client with configured AWS profile
        import os
        aws_profile = os.getenv("AWS_PROFILE")
        if aws_profile:
            session = boto3.Session(profile_name=aws_profile)
        else:
            session = boto3.Session()
        bedrock_client = session.client("bedrock", region_name="us-east-1")

        print("Checking available foundation models in Bedrock...")

        # List foundation models
        response = bedrock_client.list_foundation_models()

        claude_models = []
        for model in response.get('modelSummaries', []):
            model_id = model.get('modelId', '')
            model_name = model.get('modelName', '')
            provider_name = model.get('providerName', '')

            if 'claude' in model_id.lower() or 'anthropic' in provider_name.lower():
                claude_models.append({
                    'id': model_id,
                    'name': model_name,
                    'provider': provider_name,
                    'input_modalities': model.get('inputModalities', []),
                    'output_modalities': model.get('outputModalities', [])
                })

        if claude_models:
            print(f"\nFound {len(claude_models)} Claude/Anthropic models:")
            for model in claude_models:
                print(f"  - {model['id']} ({model['name']}) by {model['provider']}")
        else:
            print("No Claude models found.")

        # Also try to list inference profiles
        try:
            print("\nChecking inference profiles...")
            profiles_response = bedrock_client.list_inference_profiles()

            claude_profiles = []
            for profile in profiles_response.get('inferenceProfileSummaries', []):
                profile_id = profile.get('inferenceProfileId', '')
                if 'claude' in profile_id.lower() or 'anthropic' in profile_id.lower():
                    claude_profiles.append(profile)

            if claude_profiles:
                print(f"Found {len(claude_profiles)} Claude inference profiles:")
                for profile in claude_profiles:
                    print(f"  - {profile.get('inferenceProfileId')} ({profile.get('description', 'No description')})")
            else:
                print("No Claude inference profiles found.")

        except Exception as e:
            print(f"Could not list inference profiles: {e}")

        return claude_models, claude_profiles if 'claude_profiles' in locals() else []

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDeniedException':
            print("Access denied to Bedrock. Please check your AWS permissions.")
        else:
            print(f"AWS Error: {e}")
        return [], []
    except Exception as e:
        print(f"Error: {e}")
        return [], []

def test_specific_model(model_id):
    """Test a specific model to see if it's accessible."""
    import os
    try:
        from langchain_aws import ChatBedrock

        print(f"\nTesting model: {model_id}")

        # Create ChatBedrock instance
        llm = ChatBedrock(
            model_id=model_id,
            model_kwargs={
                "temperature": 0.1,
                "max_tokens": 100,
            },
            region_name="us-east-1",
            credentials_profile_name=os.getenv("AWS_PROFILE")
        )

        # Test with a simple message
        response = llm.invoke("Hello! Please respond with 'Test successful'.")
        print(f"✓ Model {model_id} works! Response: {response.content}")
        return True

    except Exception as e:
        print(f"✗ Model {model_id} failed: {e}")
        return False

if __name__ == "__main__":
    print("Bedrock Model Availability Check")
    print("=" * 40)

    models, profiles = list_available_models()

    if models or profiles:
        print(f"\nTesting a few models...")

        # Test some common model IDs that might work
        test_models = [
            "anthropic.claude-3-haiku-20240307-v1:0",
            "us.anthropic.claude-3-haiku-20240307-v1:0",
            "anthropic.claude-3-sonnet-20240229-v1:0",
            "us.anthropic.claude-3-sonnet-20240229-v1:0"
        ]

        # Add any models we found
        for model in models[:2]:  # Test first 2 models found
            test_models.append(model['id'])

        # Add any profiles we found
        for profile in profiles[:2]:  # Test first 2 profiles found
            test_models.append(profile['inferenceProfileId'])

        working_models = []
        for model_id in test_models:
            if test_specific_model(model_id):
                working_models.append(model_id)

        if working_models:
            print(f"\n🎉 Working models for your configuration:")
            for model in working_models:
                print(f"  ✓ {model}")
        else:
            print(f"\n❌ No working models found in the test set")
    else:
        print("No Claude models or profiles found in your Bedrock account.")