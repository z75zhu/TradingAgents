import chromadb
from chromadb.config import Settings
from ...bedrock_embeddings import BedrockEmbeddings


class FinancialSituationMemory:
    def __init__(self, name, config):
        self.config = config

        # Use Bedrock embeddings exclusively
        self.bedrock_embeddings = BedrockEmbeddings(config)

        # Enhanced status message with embedding method details
        if self.bedrock_embeddings.active_model:
            print(f"✅ Initialized Bedrock embeddings for memory: {name}")
            print(f"   🧠 Using AWS model: {self.bedrock_embeddings.active_model}")
        else:
            print(f"⚠️  Initialized memory: {name} with hash-based fallback")
            print(f"   💡 Consider checking AWS Bedrock model access for better quality")

        self.chroma_client = chromadb.Client(Settings(allow_reset=True))
        self.situation_collection = self.chroma_client.create_collection(name=name)

    def get_embedding(self, text):
        """Get embedding for a text using Bedrock embeddings"""
        return self.bedrock_embeddings.get_embedding(text)

    def add_situations(self, situations_and_advice):
        """Add financial situations and their corresponding advice. Parameter is a list of tuples (situation, rec)"""

        situations = []
        advice = []
        ids = []
        embeddings = []

        offset = self.situation_collection.count()

        for i, (situation, recommendation) in enumerate(situations_and_advice):
            situations.append(situation)
            advice.append(recommendation)
            ids.append(str(offset + i))
            embeddings.append(self.get_embedding(situation))

        self.situation_collection.add(
            documents=situations,
            metadatas=[{"recommendation": rec} for rec in advice],
            embeddings=embeddings,
            ids=ids,
        )

    def get_memories(self, current_situation, n_matches=1):
        """Find matching recommendations using OpenAI embeddings"""
        query_embedding = self.get_embedding(current_situation)

        results = self.situation_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_matches,
            include=["metadatas", "documents", "distances"],
        )

        matched_results = []
        for i in range(len(results["documents"][0])):
            matched_results.append(
                {
                    "matched_situation": results["documents"][0][i],
                    "recommendation": results["metadatas"][0][i]["recommendation"],
                    "similarity_score": 1 - results["distances"][0][i],
                }
            )

        return matched_results

    def test_embedding_quality(self):
        """Test the quality of embeddings for this memory instance."""
        return self.bedrock_embeddings.test_embedding_quality()

    def get_similarity(self, text1, text2):
        """Calculate similarity between two texts using Bedrock embeddings."""
        emb1 = self.get_embedding(text1)
        emb2 = self.get_embedding(text2)
        return self.bedrock_embeddings.cosine_similarity(emb1, emb2)

    def get_embedding_status(self):
        """Get detailed status of the embedding system."""
        status = {
            "provider": "AWS Bedrock",
            "active_model": self.bedrock_embeddings.active_model or "Hash Fallback",
            "is_neural_embeddings": self.bedrock_embeddings.active_model is not None,
            "aws_profile": self.bedrock_embeddings.aws_profile,
            "aws_region": self.bedrock_embeddings.aws_region,
        }

        if self.bedrock_embeddings.active_model:
            status["status"] = "✅ AWS Bedrock embeddings active"
            status["quality"] = "High - Neural embeddings"
        else:
            status["status"] = "⚠️ Using hash fallback"
            status["quality"] = "Limited - Deterministic hash method"

        return status


if __name__ == "__main__":
    # Example usage
    matcher = FinancialSituationMemory()

    # Example data
    example_data = [
        (
            "High inflation rate with rising interest rates and declining consumer spending",
            "Consider defensive sectors like consumer staples and utilities. Review fixed-income portfolio duration.",
        ),
        (
            "Tech sector showing high volatility with increasing institutional selling pressure",
            "Reduce exposure to high-growth tech stocks. Look for value opportunities in established tech companies with strong cash flows.",
        ),
        (
            "Strong dollar affecting emerging markets with increasing forex volatility",
            "Hedge currency exposure in international positions. Consider reducing allocation to emerging market debt.",
        ),
        (
            "Market showing signs of sector rotation with rising yields",
            "Rebalance portfolio to maintain target allocations. Consider increasing exposure to sectors benefiting from higher rates.",
        ),
    ]

    # Add the example situations and recommendations
    matcher.add_situations(example_data)

    # Example query
    current_situation = """
    Market showing increased volatility in tech sector, with institutional investors 
    reducing positions and rising interest rates affecting growth stock valuations
    """

    try:
        recommendations = matcher.get_memories(current_situation, n_matches=2)

        for i, rec in enumerate(recommendations, 1):
            print(f"\nMatch {i}:")
            print(f"Similarity Score: {rec['similarity_score']:.2f}")
            print(f"Matched Situation: {rec['matched_situation']}")
            print(f"Recommendation: {rec['recommendation']}")

    except Exception as e:
        print(f"Error during recommendation: {str(e)}")
