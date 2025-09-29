"""
AWS Bedrock Embeddings Implementation

Provides proper embedding functionality using AWS Titan Embed or other Bedrock embedding models
to replace the hash-based fallback in the memory system.
"""

import boto3
import json
import hashlib
import numpy as np
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BedrockEmbeddings:
    """AWS Bedrock embeddings client using Titan Embed or other available models."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.aws_profile = config.get("aws_profile", "iris-aws")
        self.aws_region = config.get("aws_region", "us-east-1")

        # Initialize Bedrock client
        try:
            if self.aws_profile:
                session = boto3.Session(profile_name=self.aws_profile)
                self.bedrock_client = session.client(
                    service_name='bedrock-runtime',
                    region_name=self.aws_region
                )
            else:
                self.bedrock_client = boto3.client(
                    service_name='bedrock-runtime',
                    region_name=self.aws_region
                )

            # Try different embedding models in order of preference
            # Based on diagnostic testing - prioritize known working models
            self.embedding_models = [
                "amazon.titan-embed-text-v2:0",    # Latest Titan Embed (tested working)
                "amazon.titan-embed-g1-text-02",   # Stable general availability model
                "cohere.embed-english-v3",         # Cohere alternative (tested working)
                "cohere.embed-multilingual-v3",    # Multilingual Cohere fallback
                "amazon.titan-embed-text-v1",      # Legacy model (may have schema issues)
            ]

            self.active_model = self._find_available_model()

        except Exception as e:
            logger.warning(f"Failed to initialize Bedrock embeddings: {e}")
            self.bedrock_client = None
            self.active_model = None

    def _find_available_model(self) -> Optional[str]:
        """Find the first available embedding model with detailed error reporting."""
        model_test_results = []

        for model in self.embedding_models:
            try:
                # Test with a simple embedding
                embedding = self._embed_text("test", model)
                if embedding and len(embedding) > 0:
                    logger.info(f"✅ Successfully initialized Bedrock embeddings with {model}")
                    return model
                else:
                    model_test_results.append(f"{model}: Empty embedding returned")
                    logger.debug(f"Model {model} returned empty embedding")
                    continue
            except Exception as e:
                error_msg = str(e)
                model_test_results.append(f"{model}: {error_msg}")

                # Log different error levels based on error type
                if "ValidationException" in error_msg:
                    logger.debug(f"Model {model} has schema validation issues: {e}")
                elif "AccessDenied" in error_msg or "UnauthorizedOperation" in error_msg:
                    logger.warning(f"Model {model} access denied - check AWS permissions: {e}")
                elif "ThrottlingException" in error_msg:
                    logger.warning(f"Model {model} throttled - try again later: {e}")
                else:
                    logger.debug(f"Model {model} not available: {e}")
                continue

        # Log detailed results if no models worked
        logger.warning("No Bedrock embedding models available, falling back to enhanced hash method")
        logger.info("Model test results:")
        for result in model_test_results:
            logger.info(f"  • {result}")

        return None

    def _embed_text(self, text: str, model_id: str) -> List[float]:
        """Embed text using a specific Bedrock model."""
        if not self.bedrock_client:
            raise Exception("Bedrock client not available")

        # Prepare request based on model type with model-specific optimizations
        if "titan-embed-text-v2" in model_id.lower():
            # Titan Embed v2 supports custom dimensions and normalization
            body = json.dumps({
                "inputText": text,
                "dimensions": 1024,
                "normalize": True
            })
        elif "titan-embed-g1-text" in model_id.lower():
            # General availability Titan model - simpler format
            body = json.dumps({
                "inputText": text
            })
        elif "titan-embed-text-v1" in model_id.lower():
            # Legacy Titan v1 - basic format only
            body = json.dumps({
                "inputText": text
            })
        elif "cohere" in model_id.lower():
            # Cohere models - array format
            body = json.dumps({
                "texts": [text],
                "input_type": "search_document"
            })
        else:
            # Generic fallback
            body = json.dumps({"inputText": text})

        try:
            response = self.bedrock_client.invoke_model(
                body=body,
                modelId=model_id,
                accept='application/json',
                contentType='application/json'
            )

            response_body = json.loads(response.get('body').read())

            # Extract embeddings based on model response format
            if "titan" in model_id.lower():
                return response_body.get('embedding', [])
            elif "cohere" in model_id.lower():
                return response_body.get('embeddings', [[]]) [0]
            else:
                return response_body.get('embedding', [])

        except Exception as e:
            raise Exception(f"Failed to embed text with {model_id}: {str(e)}")

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using only Bedrock models."""
        if not text or not text.strip():
            raise ValueError("Cannot create embedding for empty or whitespace-only text")

        # Only use Bedrock models - no hash fallbacks for consistent quality
        if not self.active_model or not self.bedrock_client:
            raise RuntimeError(
                "AWS Bedrock embeddings are not available. "
                "Please check your AWS configuration, permissions, and model access. "
                "Hash-based fallbacks have been removed to ensure consistent data quality."
            )

        try:
            embedding = self._embed_text(text, self.active_model)
            if not embedding:
                raise RuntimeError(f"Bedrock model {self.active_model} returned empty embedding")
            return embedding
        except Exception as e:
            logger.error(f"Bedrock embedding failed for model {self.active_model}: {e}")
            raise RuntimeError(
                f"Failed to generate embedding using Bedrock model {self.active_model}: {str(e)}"
            )


    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts."""
        return [self.get_embedding(text) for text in texts]

    def cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        if len(embedding1) != len(embedding2):
            return 0.0

        # Convert to numpy arrays for easier calculation
        a = np.array(embedding1)
        b = np.array(embedding2)

        # Calculate cosine similarity
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def test_embedding_quality(self) -> Dict[str, Any]:
        """Test the quality of embeddings with comprehensive financial text samples."""
        import time

        # Enhanced test cases with expected similarity ranges
        test_cases = [
            # High similarity pairs (should be > 0.4)
            ("Apple stock is performing well", "AAPL shares are rising", "high"),
            ("Market volatility is high", "Stock market is very unstable", "high"),
            ("Federal Reserve raises interest rates", "Central bank increases rates", "high"),
            ("Tesla earnings exceeded expectations", "TSLA reported strong profits", "high"),

            # Medium similarity pairs (should be 0.2-0.4)
            ("Apple quarterly results", "Technology sector performance", "medium"),
            ("Interest rate decision", "Banking industry outlook", "medium"),

            # Low similarity pairs (should be < 0.2)
            ("Apple stock price", "Weather forecast sunny", "low"),
            ("Federal Reserve policy", "Sports game results", "low"),
        ]

        if not self.active_model:
            return {
                "model_used": "none",
                "is_bedrock_embeddings": False,
                "error": "No Bedrock embedding models available. Hash fallbacks have been removed.",
                "recommendation": "Check AWS configuration, permissions, and model access."
            }

        results = {
            "model_used": self.active_model,
            "is_bedrock_embeddings": True,
            "embedding_dimension": None,
            "avg_response_time": None,
            "quality_score": None,
            "similarities": [],
            "performance_metrics": {}
        }

        response_times = []
        quality_scores = []

        for text1, text2, expected_category in test_cases:
            start_time = time.time()

            emb1 = self.get_embedding(text1)
            emb2 = self.get_embedding(text2)

            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to ms
            response_times.append(response_time)

            if results["embedding_dimension"] is None:
                results["embedding_dimension"] = len(emb1)

            similarity = self.cosine_similarity(emb1, emb2)

            # Calculate quality score based on expected category
            if expected_category == "high" and similarity > 0.4:
                quality_score = 1.0
            elif expected_category == "medium" and 0.2 <= similarity <= 0.4:
                quality_score = 1.0
            elif expected_category == "low" and similarity < 0.2:
                quality_score = 1.0
            else:
                # Partial credit based on how close we are to expected range
                if expected_category == "high":
                    quality_score = max(0, similarity / 0.4)
                elif expected_category == "medium":
                    quality_score = max(0, 1 - abs(similarity - 0.3) / 0.3)
                else:  # low
                    quality_score = max(0, (0.2 - similarity) / 0.2)

            quality_scores.append(quality_score)

            results["similarities"].append({
                "text1": text1,
                "text2": text2,
                "similarity": similarity,
                "expected_category": expected_category,
                "quality_score": quality_score,
                "response_time_ms": response_time
            })

        # Calculate aggregate metrics
        results["avg_response_time"] = sum(response_times) / len(response_times)
        results["quality_score"] = sum(quality_scores) / len(quality_scores)

        results["performance_metrics"] = {
            "total_tests": len(test_cases),
            "avg_response_time_ms": results["avg_response_time"],
            "min_response_time_ms": min(response_times),
            "max_response_time_ms": max(response_times),
            "quality_percentage": results["quality_score"] * 100,
            "embedding_method": "AWS Bedrock"
        }

        return results