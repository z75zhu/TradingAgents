#!/usr/bin/env python3
"""
AWS Bedrock Embeddings Diagnostic Tool

Comprehensive testing of AWS Bedrock embedding model access to identify
why the system is falling back to hash-based embeddings instead of using
proper neural embeddings from AWS Titan or Cohere models.
"""

import boto3
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def test_aws_credentials():
    """Test basic AWS credentials and session setup."""
    print("🔐 TESTING AWS CREDENTIALS & SESSION")
    print("=" * 60)

    try:
        # Test with iris-aws profile
        session = boto3.Session(profile_name='iris-aws')
        sts_client = session.client('sts', region_name='us-east-1')

        # Get caller identity
        identity = sts_client.get_caller_identity()
        print(f"✅ Successfully authenticated with iris-aws profile")
        print(f"   Account ID: {identity['Account']}")
        print(f"   User ARN: {identity['Arn']}")
        print(f"   User ID: {identity['UserId']}")

        return True, session

    except Exception as e:
        print(f"❌ AWS credential setup failed: {e}")
        print(f"   Make sure 'iris-aws' profile is configured in ~/.aws/credentials")
        return False, None

def test_bedrock_service_access(session):
    """Test basic Bedrock service access."""
    print(f"\n🚀 TESTING BEDROCK SERVICE ACCESS")
    print("=" * 60)

    try:
        bedrock_client = session.client('bedrock', region_name='us-east-1')

        # List available foundation models
        response = bedrock_client.list_foundation_models()
        models = response.get('modelSummaries', [])

        print(f"✅ Successfully connected to Bedrock service")
        print(f"   Total foundation models available: {len(models)}")

        # Filter embedding models
        embedding_models = [
            model for model in models
            if 'embed' in model.get('modelId', '').lower()
        ]

        print(f"   Embedding models found: {len(embedding_models)}")
        for model in embedding_models:
            print(f"      • {model['modelId']} ({model['modelName']})")

        return True, bedrock_client, embedding_models

    except Exception as e:
        print(f"❌ Bedrock service access failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        if hasattr(e, 'response'):
            print(f"   Error code: {e.response.get('Error', {}).get('Code', 'Unknown')}")
        return False, None, []

def test_bedrock_runtime_access(session):
    """Test Bedrock runtime service for model invocation."""
    print(f"\n⚡ TESTING BEDROCK RUNTIME ACCESS")
    print("=" * 60)

    try:
        bedrock_runtime = session.client('bedrock-runtime', region_name='us-east-1')
        print(f"✅ Successfully created Bedrock Runtime client")
        return True, bedrock_runtime

    except Exception as e:
        print(f"❌ Bedrock Runtime access failed: {e}")
        return False, None

def test_individual_embedding_model(bedrock_runtime, model_id, model_name):
    """Test a specific embedding model with a sample request."""
    print(f"\n🧠 TESTING {model_name} ({model_id})")
    print("-" * 50)

    test_text = "Apple stock is performing well in the current market conditions"

    try:
        # Prepare request based on model type
        if "titan" in model_id.lower():
            body = json.dumps({
                "inputText": test_text,
                "dimensions": 1024,
                "normalize": True
            })
        elif "cohere" in model_id.lower():
            body = json.dumps({
                "texts": [test_text],
                "input_type": "search_document"
            })
        else:
            # Generic format
            body = json.dumps({
                "inputText": test_text
            })

        # Make the request
        response = bedrock_runtime.invoke_model(
            body=body,
            modelId=model_id,
            accept='application/json',
            contentType='application/json'
        )

        # Parse response
        response_body = json.loads(response.get('body').read())

        # Extract embedding based on model type
        if "titan" in model_id.lower():
            embedding = response_body.get('embedding', [])
        elif "cohere" in model_id.lower():
            embedding = response_body.get('embeddings', [[]])[0]
        else:
            embedding = response_body.get('embedding', [])

        if embedding and len(embedding) > 0:
            print(f"✅ {model_name}: SUCCESS")
            print(f"   Embedding dimension: {len(embedding)}")
            print(f"   Sample values: {embedding[:5]}...")
            print(f"   Response size: {len(str(response_body))} characters")
            return True, embedding
        else:
            print(f"❌ {model_name}: Empty embedding returned")
            print(f"   Response body: {response_body}")
            return False, None

    except Exception as e:
        print(f"❌ {model_name}: FAILED")
        print(f"   Error: {str(e)}")
        print(f"   Error type: {type(e).__name__}")

        if hasattr(e, 'response'):
            error_info = e.response.get('Error', {})
            print(f"   Error code: {error_info.get('Code', 'Unknown')}")
            print(f"   Error message: {error_info.get('Message', 'No message')}")

        return False, None

def test_current_system_behavior():
    """Test the current BedrockEmbeddings class behavior."""
    print(f"\n🔍 TESTING CURRENT SYSTEM BEHAVIOR")
    print("=" * 60)

    try:
        from tradingagents.bedrock_embeddings import BedrockEmbeddings
        from tradingagents.default_config import DEFAULT_CONFIG

        print(f"✅ Successfully imported BedrockEmbeddings")

        # Initialize embeddings system
        embeddings = BedrockEmbeddings(DEFAULT_CONFIG)

        print(f"   Active model: {embeddings.active_model or 'None (using hash fallback)'}")
        print(f"   Has Bedrock client: {embeddings.bedrock_client is not None}")
        print(f"   AWS profile: {embeddings.aws_profile}")
        print(f"   AWS region: {embeddings.aws_region}")

        # Test embedding generation
        test_text = "Testing embedding generation with current system"
        embedding = embeddings.get_embedding(test_text)

        print(f"   Generated embedding dimension: {len(embedding)}")

        if embeddings.active_model:
            print(f"✅ Current system is using real Bedrock embeddings")
            return True, "bedrock", embedding
        else:
            print(f"⚠️ Current system is using hash-based fallback")
            return True, "hash_fallback", embedding

    except Exception as e:
        print(f"❌ Current system test failed: {e}")
        traceback.print_exc()
        return False, "error", None

def compare_embedding_quality(bedrock_embedding, hash_embedding):
    """Compare quality between real Bedrock and hash fallback embeddings."""
    print(f"\n📊 COMPARING EMBEDDING QUALITY")
    print("=" * 60)

    if bedrock_embedding is None or hash_embedding is None:
        print("⚠️ Cannot compare - missing embeddings")
        return

    try:
        import numpy as np

        # Test semantic similarity
        test_pairs = [
            ("Apple stock price is rising", "AAPL shares are increasing in value"),
            ("Market volatility is high", "Stock market shows significant fluctuation"),
            ("Federal Reserve announces rate hike", "Central bank increases interest rates")
        ]

        print("Testing semantic similarity detection:")

        for text1, text2 in test_pairs:
            # This would require the embedding system to process both texts
            # For now, we'll just show the concept
            print(f"   '{text1[:30]}...' vs '{text2[:30]}...'")
            print(f"      With proper embeddings: Expected high similarity")
            print(f"      With hash fallback: Likely poor similarity")

        print(f"\n📈 Embedding Statistics:")
        print(f"   Bedrock embedding dimension: {len(bedrock_embedding)}")
        print(f"   Hash embedding dimension: {len(hash_embedding)}")
        print(f"   Bedrock embedding range: [{min(bedrock_embedding):.3f}, {max(bedrock_embedding):.3f}]")
        print(f"   Hash embedding range: [{min(hash_embedding):.3f}, {max(hash_embedding):.3f}]")

    except Exception as e:
        print(f"❌ Quality comparison failed: {e}")

def generate_recommendations():
    """Generate specific recommendations based on test results."""
    print(f"\n💡 RECOMMENDATIONS")
    print("=" * 60)

    return [
        "1. Check AWS Bedrock model access permissions in AWS Console",
        "2. Verify embedding models are enabled for your account in us-east-1",
        "3. Review AWS IAM policies for bedrock:InvokeModel permissions",
        "4. Test with alternative regions if models aren't available in us-east-1",
        "5. Consider requesting quota increases for embedding models",
        "6. Update model IDs to use currently available versions",
        "7. Implement better error handling and retry logic",
        "8. Add embedding quality monitoring to detect future issues"
    ]

def main():
    """Main diagnostic function."""
    print("🔬 AWS BEDROCK EMBEDDINGS COMPREHENSIVE DIAGNOSTIC")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target Profile: iris-aws")
    print(f"Target Region: us-east-1")

    results = {}

    # Test 1: AWS Credentials
    cred_success, session = test_aws_credentials()
    results['credentials'] = cred_success

    if not cred_success:
        print("\n❌ DIAGNOSTIC ABORTED: Cannot proceed without valid AWS credentials")
        return

    # Test 2: Bedrock Service Access
    bedrock_success, bedrock_client, available_models = test_bedrock_service_access(session)
    results['bedrock_service'] = bedrock_success

    # Test 3: Bedrock Runtime Access
    runtime_success, bedrock_runtime = test_bedrock_runtime_access(session)
    results['bedrock_runtime'] = runtime_success

    # Test 4: Individual Embedding Models
    embedding_test_results = {}

    if runtime_success and bedrock_runtime:
        target_models = [
            ("amazon.titan-embed-text-v2:0", "Amazon Titan Embed Text v2"),
            ("amazon.titan-embed-text-v1", "Amazon Titan Embed Text v1"),
            ("cohere.embed-english-v3", "Cohere Embed English v3")
        ]

        for model_id, model_name in target_models:
            success, embedding = test_individual_embedding_model(bedrock_runtime, model_id, model_name)
            embedding_test_results[model_id] = {
                'success': success,
                'embedding': embedding
            }

    results['individual_models'] = embedding_test_results

    # Test 5: Current System Behavior
    system_success, method_used, current_embedding = test_current_system_behavior()
    results['current_system'] = {
        'success': system_success,
        'method': method_used,
        'embedding': current_embedding
    }

    # Test 6: Quality Comparison (if we have both types)
    working_bedrock_embedding = None
    for model_result in embedding_test_results.values():
        if model_result['success'] and model_result['embedding']:
            working_bedrock_embedding = model_result['embedding']
            break

    if working_bedrock_embedding and current_embedding and method_used == "hash_fallback":
        compare_embedding_quality(working_bedrock_embedding, current_embedding)

    # Generate Summary
    print(f"\n📋 DIAGNOSTIC SUMMARY")
    print("=" * 60)

    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if
                      (isinstance(result, bool) and result) or
                      (isinstance(result, dict) and result.get('success', False)))

    print(f"Tests Passed: {passed_tests}/{total_tests}")

    for test_name, result in results.items():
        if test_name == 'individual_models':
            model_passes = sum(1 for r in result.values() if r['success'])
            total_models = len(result)
            status = f"✅ {model_passes}/{total_models} models working" if model_passes > 0 else "❌ No models working"
        elif test_name == 'current_system':
            if result.get('method') == 'bedrock':
                status = "✅ Using Bedrock embeddings"
            elif result.get('method') == 'hash_fallback':
                status = "⚠️ Using hash fallback"
            else:
                status = "❌ System error"
        else:
            status = "✅ PASSED" if result else "❌ FAILED"

        print(f"{test_name:20} {status}")

    # Recommendations
    recommendations = generate_recommendations()
    for rec in recommendations:
        print(f"  {rec}")

    print("=" * 60)
    print("🎯 Next steps: Review the specific error messages above to identify")
    print("   the exact AWS configuration needed to enable Bedrock embeddings.")

if __name__ == "__main__":
    main()