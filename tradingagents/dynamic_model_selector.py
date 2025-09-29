"""
Dynamic Bedrock Model Selection Strategy

This module implements intelligent model selection for different trading tasks,
choosing between Claude models (Haiku, Sonnet, Opus) based on:
- Task complexity
- Processing requirements
- Cost optimization
- Performance needs
"""

from enum import Enum
from typing import Dict, Any, Optional, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    """Defines different levels of task complexity for model selection."""
    SIMPLE = "simple"          # Basic data retrieval, simple calculations
    MODERATE = "moderate"      # Analysis, pattern recognition, moderate reasoning
    COMPLEX = "complex"        # Deep analysis, multi-step reasoning, trading decisions
    CRITICAL = "critical"      # High-stakes decisions, comprehensive analysis


class ModelTier(Enum):
    """Available Claude model tiers with their characteristics."""
    HAIKU = {
        "model_id": "claude-3-5-haiku-latest",
        "cost": "low",
        "speed": "fast",
        "reasoning": "basic",
        "use_case": "Simple tasks, data formatting, quick responses"
    }
    SONNET = {
        "model_id": "claude-3-5-sonnet-latest",
        "cost": "medium",
        "speed": "medium",
        "reasoning": "advanced",
        "use_case": "Analysis, research, moderate complexity reasoning"
    }
    OPUS = {
        "model_id": "claude-opus-4-0",
        "cost": "high",
        "speed": "slow",
        "reasoning": "superior",
        "use_case": "Complex analysis, critical decisions, deep reasoning"
    }


class DynamicModelSelector:
    """
    Intelligent model selector that chooses the optimal Claude model
    for different trading agent tasks.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.usage_stats = {}
        self.performance_history = {}

        # Task-to-complexity mapping
        self.task_complexity_map = {
            # Simple tasks - use Haiku
            "data_retrieval": TaskComplexity.SIMPLE,
            "data_formatting": TaskComplexity.SIMPLE,
            "basic_calculations": TaskComplexity.SIMPLE,
            "status_updates": TaskComplexity.SIMPLE,

            # Moderate tasks - use Sonnet
            "market_analysis": TaskComplexity.MODERATE,
            "news_sentiment": TaskComplexity.MODERATE,
            "technical_indicators": TaskComplexity.MODERATE,
            "earnings_analysis": TaskComplexity.MODERATE,
            "research_synthesis": TaskComplexity.MODERATE,

            # Complex tasks - use Sonnet (high-performance)
            "investment_research": TaskComplexity.COMPLEX,
            "debate_analysis": TaskComplexity.COMPLEX,
            "risk_assessment": TaskComplexity.COMPLEX,
            "pattern_recognition": TaskComplexity.COMPLEX,

            # Critical tasks - use Opus
            "final_trading_decision": TaskComplexity.CRITICAL,
            "portfolio_allocation": TaskComplexity.CRITICAL,
            "risk_management_decision": TaskComplexity.CRITICAL,
            "judge_final_verdict": TaskComplexity.CRITICAL,
        }

        # Model selection strategy
        self.complexity_to_model = {
            TaskComplexity.SIMPLE: ModelTier.HAIKU,
            TaskComplexity.MODERATE: ModelTier.SONNET,
            TaskComplexity.COMPLEX: ModelTier.SONNET,  # Use high-performance Sonnet
            TaskComplexity.CRITICAL: ModelTier.OPUS,   # Use Opus for critical decisions
        }

        # Performance thresholds for dynamic adjustment
        self.performance_thresholds = {
            "accuracy_threshold": 0.85,
            "response_time_threshold": 30.0,  # seconds
            "cost_optimization_enabled": True,
        }

    def select_model_for_task(
        self,
        task_type: str,
        context: Optional[Dict[str, Any]] = None,
        force_model: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Select the optimal model for a given task.

        Args:
            task_type: Type of task being performed
            context: Additional context for decision making
            force_model: Force a specific model (for testing/debugging)

        Returns:
            Tuple of (model_id, reasoning)
        """
        if force_model:
            return force_model, f"Forced selection: {force_model}"

        # Get task complexity
        complexity = self.task_complexity_map.get(task_type, TaskComplexity.MODERATE)

        # Apply dynamic adjustments based on context
        if context:
            complexity = self._adjust_complexity_for_context(complexity, context)

        # Select model based on complexity
        selected_model = self.complexity_to_model[complexity]
        model_id = selected_model.value["model_id"]

        # Apply cost optimization if enabled
        if self.performance_thresholds["cost_optimization_enabled"]:
            model_id = self._apply_cost_optimization(model_id, task_type, context)

        reasoning = self._generate_selection_reasoning(task_type, complexity, selected_model, context)

        # Log the selection
        self._log_model_selection(task_type, model_id, complexity, reasoning)

        return model_id, reasoning

    def _adjust_complexity_for_context(
        self,
        base_complexity: TaskComplexity,
        context: Dict[str, Any]
    ) -> TaskComplexity:
        """Adjust complexity based on contextual factors."""

        # Market volatility factor
        if context.get("market_volatility") == "high":
            if base_complexity in [TaskComplexity.COMPLEX, TaskComplexity.MODERATE]:
                return TaskComplexity.CRITICAL

        # Data volume factor
        data_volume = context.get("data_volume", "medium")
        if data_volume == "large" and base_complexity == TaskComplexity.MODERATE:
            return TaskComplexity.COMPLEX

        # Time sensitivity factor
        if context.get("time_sensitive", False):
            if base_complexity == TaskComplexity.CRITICAL:
                return TaskComplexity.COMPLEX  # Use faster Sonnet instead of Opus

        # Multi-agent coordination factor
        if context.get("multi_agent_task", False):
            if base_complexity == TaskComplexity.SIMPLE:
                return TaskComplexity.MODERATE

        return base_complexity

    def _apply_cost_optimization(
        self,
        model_id: str,
        task_type: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Apply cost optimization strategies."""

        # Check if we can use a cheaper model based on recent performance
        if model_id == ModelTier.OPUS.value["model_id"]:
            # Check if Sonnet has been performing well for similar tasks
            sonnet_performance = self._get_recent_performance(
                ModelTier.SONNET.value["model_id"],
                task_type
            )
            if sonnet_performance and sonnet_performance > self.performance_thresholds["accuracy_threshold"]:
                logger.info(f"Cost optimization: Using Sonnet instead of Opus for {task_type}")
                return ModelTier.SONNET.value["model_id"]

        # During off-peak hours, we might use higher-tier models for better results
        current_hour = datetime.now().hour
        if 2 <= current_hour <= 6:  # Off-peak hours
            if model_id == ModelTier.HAIKU.value["model_id"]:
                logger.info(f"Off-peak optimization: Upgrading to Sonnet for {task_type}")
                return ModelTier.SONNET.value["model_id"]

        return model_id

    def _generate_selection_reasoning(
        self,
        task_type: str,
        complexity: TaskComplexity,
        selected_model: ModelTier,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Generate human-readable reasoning for model selection."""

        reasoning_parts = [
            f"Task '{task_type}' classified as {complexity.value} complexity",
            f"Selected {selected_model.name} model ({selected_model.value['model_id']})",
            f"Reasoning: {selected_model.value['use_case']}"
        ]

        if context:
            context_factors = []
            if context.get("market_volatility") == "high":
                context_factors.append("high market volatility")
            if context.get("time_sensitive"):
                context_factors.append("time-sensitive task")
            if context.get("multi_agent_task"):
                context_factors.append("multi-agent coordination required")

            if context_factors:
                reasoning_parts.append(f"Context factors: {', '.join(context_factors)}")

        return " | ".join(reasoning_parts)

    def _get_recent_performance(self, model_id: str, task_type: str) -> Optional[float]:
        """Get recent performance metrics for a model-task combination."""
        key = f"{model_id}_{task_type}"
        return self.performance_history.get(key, {}).get("recent_accuracy")

    def _log_model_selection(
        self,
        task_type: str,
        model_id: str,
        complexity: TaskComplexity,
        reasoning: str
    ):
        """Log model selection for analytics and debugging."""

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "task_type": task_type,
            "selected_model": model_id,
            "complexity": complexity.value,
            "reasoning": reasoning
        }

        # Update usage statistics
        if model_id not in self.usage_stats:
            self.usage_stats[model_id] = {"count": 0, "tasks": {}}
        self.usage_stats[model_id]["count"] += 1

        if task_type not in self.usage_stats[model_id]["tasks"]:
            self.usage_stats[model_id]["tasks"][task_type] = 0
        self.usage_stats[model_id]["tasks"][task_type] += 1

        logger.info(f"Model selection: {reasoning}")

    def get_usage_statistics(self) -> Dict[str, Any]:
        """Get current usage statistics for analysis."""
        return {
            "usage_stats": self.usage_stats,
            "performance_history": self.performance_history,
            "total_selections": sum(stats["count"] for stats in self.usage_stats.values())
        }

    def update_performance_metrics(
        self,
        model_id: str,
        task_type: str,
        accuracy: float,
        response_time: float
    ):
        """Update performance metrics for continuous improvement."""
        key = f"{model_id}_{task_type}"

        if key not in self.performance_history:
            self.performance_history[key] = {
                "accuracy_history": [],
                "response_time_history": [],
                "recent_accuracy": 0.0,
                "recent_response_time": 0.0
            }

        history = self.performance_history[key]
        history["accuracy_history"].append(accuracy)
        history["response_time_history"].append(response_time)

        # Keep only recent history (last 10 runs)
        if len(history["accuracy_history"]) > 10:
            history["accuracy_history"] = history["accuracy_history"][-10:]
        if len(history["response_time_history"]) > 10:
            history["response_time_history"] = history["response_time_history"][-10:]

        # Calculate recent averages
        history["recent_accuracy"] = sum(history["accuracy_history"]) / len(history["accuracy_history"])
        history["recent_response_time"] = sum(history["response_time_history"]) / len(history["response_time_history"])

    def get_recommended_model_for_agent(self, agent_role: str) -> str:
        """Get recommended model for specific agent roles."""

        agent_model_map = {
            # Simple agents use Haiku
            "data_fetcher": ModelTier.HAIKU.value["model_id"],
            "formatter": ModelTier.HAIKU.value["model_id"],

            # Analysis agents use Sonnet
            "market_analyst": ModelTier.SONNET.value["model_id"],
            "news_analyst": ModelTier.SONNET.value["model_id"],
            "social_analyst": ModelTier.SONNET.value["model_id"],
            "fundamentals_analyst": ModelTier.SONNET.value["model_id"],
            "bull_researcher": ModelTier.SONNET.value["model_id"],
            "bear_researcher": ModelTier.SONNET.value["model_id"],

            # Decision agents use Opus for critical thinking
            "investment_judge": ModelTier.OPUS.value["model_id"],
            "risk_manager": ModelTier.OPUS.value["model_id"],
            "portfolio_manager": ModelTier.OPUS.value["model_id"],
            "trader": ModelTier.SONNET.value["model_id"],  # Sonnet for speed in execution
        }

        return agent_model_map.get(agent_role, ModelTier.SONNET.value["model_id"])