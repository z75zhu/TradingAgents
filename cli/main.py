from typing import Optional, Dict, Any
import datetime
import typer
from pathlib import Path
from functools import wraps
from rich.console import Console
from rich.panel import Panel
from rich.spinner import Spinner
from rich.live import Live
from rich.columns import Columns
from rich.markdown import Markdown
from rich.layout import Layout
from rich.text import Text
from rich.live import Live
from rich.table import Table
from collections import deque
import time
from rich.tree import Tree
from rich import box
from rich.align import Align
from rich.rule import Rule

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from cli.models import AnalystType
from cli.utils import *

console = Console()

app = typer.Typer(
    name="TradingAgents",
    help="TradingAgents CLI: Multi-Agents LLM Financial Trading Framework",
    add_completion=True,  # Enable shell completion
)


# Create a deque to store recent messages with a maximum length
class MessageBuffer:
    def __init__(self, max_length=100):
        self.messages = deque(maxlen=max_length)
        self.tool_calls = deque(maxlen=max_length)
        self.current_report = None
        self.final_report = None  # Store the complete final report
        self.agent_status = {
            # Analyst Team
            "Market Analyst": "pending",
            "Social Analyst": "pending",
            "News Analyst": "pending",
            "Fundamentals Analyst": "pending",
            # Research Team
            "Bull Researcher": "pending",
            "Bear Researcher": "pending",
            "Research Manager": "pending",
            # Trading Team
            "Trader": "pending",
            # Risk Management Team
            "Risky Analyst": "pending",
            "Neutral Analyst": "pending",
            "Safe Analyst": "pending",
            # Portfolio Management Team
            "Portfolio Manager": "pending",
        }
        self.current_agent = None
        self.report_sections = {
            "market_report": None,
            "sentiment_report": None,
            "news_report": None,
            "fundamentals_report": None,
            "investment_plan": None,
            "trader_investment_plan": None,
            "final_trade_decision": None,
        }

    def add_message(self, message_type, content):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.messages.append((timestamp, message_type, content))

    def add_tool_call(self, tool_name, args):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.tool_calls.append((timestamp, tool_name, args))

    def update_agent_status(self, agent, status):
        if agent in self.agent_status:
            self.agent_status[agent] = status
            self.current_agent = agent

    def update_report_section(self, section_name, content):
        if section_name in self.report_sections:
            self.report_sections[section_name] = content
            self._update_current_report()

    def _update_current_report(self):
        # For the panel display, only show the most recently updated section
        latest_section = None
        latest_content = None

        # Find the most recently updated section
        for section, content in self.report_sections.items():
            if content is not None:
                latest_section = section
                latest_content = content
               
        if latest_section and latest_content:
            # Format the current section for display
            section_titles = {
                "market_report": "Market Analysis",
                "sentiment_report": "Social Sentiment",
                "news_report": "News Analysis",
                "fundamentals_report": "Fundamentals Analysis",
                "investment_plan": "Research Team Decision",
                "trader_investment_plan": "Trading Team Plan",
                "final_trade_decision": "Portfolio Management Decision",
            }
            self.current_report = (
                f"### {section_titles[latest_section]}\n{latest_content}"
            )

        # Update the final complete report
        self._update_final_report()

    def _update_final_report(self):
        report_parts = []

        # Analyst Team Reports
        if any(
            self.report_sections[section]
            for section in [
                "market_report",
                "sentiment_report",
                "news_report",
                "fundamentals_report",
            ]
        ):
            report_parts.append("## Analyst Team Reports")
            if self.report_sections["market_report"]:
                report_parts.append(
                    f"### Market Analysis\n{self.report_sections['market_report']}"
                )
            if self.report_sections["sentiment_report"]:
                report_parts.append(
                    f"### Social Sentiment\n{self.report_sections['sentiment_report']}"
                )
            if self.report_sections["news_report"]:
                report_parts.append(
                    f"### News Analysis\n{self.report_sections['news_report']}"
                )
            if self.report_sections["fundamentals_report"]:
                report_parts.append(
                    f"### Fundamentals Analysis\n{self.report_sections['fundamentals_report']}"
                )

        # Research Team Reports
        if self.report_sections["investment_plan"]:
            report_parts.append("## Research Team Decision")
            report_parts.append(f"{self.report_sections['investment_plan']}")

        # Trading Team Reports
        if self.report_sections["trader_investment_plan"]:
            report_parts.append("## Trading Team Plan")
            report_parts.append(f"{self.report_sections['trader_investment_plan']}")

        # Portfolio Management Decision
        if self.report_sections["final_trade_decision"]:
            report_parts.append("## Portfolio Management Decision")
            report_parts.append(f"{self.report_sections['final_trade_decision']}")

        self.final_report = "\n\n".join(report_parts) if report_parts else None


message_buffer = MessageBuffer()


def create_layout():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3),
    )
    layout["main"].split_column(
        Layout(name="upper", ratio=3), Layout(name="analysis", ratio=5)
    )
    layout["upper"].split_row(
        Layout(name="progress", ratio=2), Layout(name="messages", ratio=3)
    )
    return layout


def update_display(layout, spinner_text=None):
    # Header with welcome message
    layout["header"].update(
        Panel(
            "[bold green]Welcome to TradingAgents CLI[/bold green]\n"
            "[dim]© [Tauric Research](https://github.com/TauricResearch)[/dim]",
            title="Welcome to TradingAgents",
            border_style="green",
            padding=(1, 2),
            expand=True,
        )
    )

    # Progress panel showing agent status
    progress_table = Table(
        show_header=True,
        header_style="bold magenta",
        show_footer=False,
        box=box.SIMPLE_HEAD,  # Use simple header with horizontal lines
        title=None,  # Remove the redundant Progress title
        padding=(0, 2),  # Add horizontal padding
        expand=True,  # Make table expand to fill available space
    )
    progress_table.add_column("Team", style="cyan", justify="center", width=20)
    progress_table.add_column("Agent", style="green", justify="center", width=20)
    progress_table.add_column("Status", style="yellow", justify="center", width=20)

    # Group agents by team
    teams = {
        "Analyst Team": [
            "Market Analyst",
            "Social Analyst",
            "News Analyst",
            "Fundamentals Analyst",
        ],
        "Research Team": ["Bull Researcher", "Bear Researcher", "Research Manager"],
        "Trading Team": ["Trader"],
        "Risk Management": ["Risky Analyst", "Neutral Analyst", "Safe Analyst"],
        "Portfolio Management": ["Portfolio Manager"],
    }

    for team, agents in teams.items():
        # Add first agent with team name
        first_agent = agents[0]
        status = message_buffer.agent_status[first_agent]
        if status == "in_progress":
            spinner = Spinner(
                "dots", text="[blue]in_progress[/blue]", style="bold cyan"
            )
            status_cell = spinner
        else:
            status_color = {
                "pending": "yellow",
                "completed": "green",
                "error": "red",
            }.get(status, "white")
            status_cell = f"[{status_color}]{status}[/{status_color}]"
        progress_table.add_row(team, first_agent, status_cell)

        # Add remaining agents in team
        for agent in agents[1:]:
            status = message_buffer.agent_status[agent]
            if status == "in_progress":
                spinner = Spinner(
                    "dots", text="[blue]in_progress[/blue]", style="bold cyan"
                )
                status_cell = spinner
            else:
                status_color = {
                    "pending": "yellow",
                    "completed": "green",
                    "error": "red",
                }.get(status, "white")
                status_cell = f"[{status_color}]{status}[/{status_color}]"
            progress_table.add_row("", agent, status_cell)

        # Add horizontal line after each team
        progress_table.add_row("─" * 20, "─" * 20, "─" * 20, style="dim")

    layout["progress"].update(
        Panel(progress_table, title="Progress", border_style="cyan", padding=(1, 2))
    )

    # Messages panel showing recent messages and tool calls
    messages_table = Table(
        show_header=True,
        header_style="bold magenta",
        show_footer=False,
        expand=True,  # Make table expand to fill available space
        box=box.MINIMAL,  # Use minimal box style for a lighter look
        show_lines=True,  # Keep horizontal lines
        padding=(0, 1),  # Add some padding between columns
    )
    messages_table.add_column("Time", style="cyan", width=8, justify="center")
    messages_table.add_column("Type", style="green", width=10, justify="center")
    messages_table.add_column(
        "Content", style="white", no_wrap=False, ratio=1
    )  # Make content column expand

    # Combine tool calls and messages
    all_messages = []

    # Add tool calls
    for timestamp, tool_name, args in message_buffer.tool_calls:
        # Truncate tool call args if too long
        if isinstance(args, str) and len(args) > 100:
            args = args[:97] + "..."
        all_messages.append((timestamp, "Tool", f"{tool_name}: {args}"))

    # Add regular messages
    for timestamp, msg_type, content in message_buffer.messages:
        # Convert content to string if it's not already
        content_str = content
        if isinstance(content, list):
            # Handle list of content blocks (Anthropic format)
            text_parts = []
            for item in content:
                if isinstance(item, dict):
                    if item.get('type') == 'text':
                        text_parts.append(item.get('text', ''))
                    elif item.get('type') == 'tool_use':
                        text_parts.append(f"[Tool: {item.get('name', 'unknown')}]")
                else:
                    text_parts.append(str(item))
            content_str = ' '.join(text_parts)
        elif not isinstance(content_str, str):
            content_str = str(content)
            
        # Truncate message content if too long
        if len(content_str) > 200:
            content_str = content_str[:197] + "..."
        all_messages.append((timestamp, msg_type, content_str))

    # Sort by timestamp
    all_messages.sort(key=lambda x: x[0])

    # Calculate how many messages we can show based on available space
    # Start with a reasonable number and adjust based on content length
    max_messages = 12  # Increased from 8 to better fill the space

    # Get the last N messages that will fit in the panel
    recent_messages = all_messages[-max_messages:]

    # Add messages to table
    for timestamp, msg_type, content in recent_messages:
        # Format content with word wrapping
        wrapped_content = Text(content, overflow="fold")
        messages_table.add_row(timestamp, msg_type, wrapped_content)

    if spinner_text:
        messages_table.add_row("", "Spinner", spinner_text)

    # Add a footer to indicate if messages were truncated
    if len(all_messages) > max_messages:
        messages_table.footer = (
            f"[dim]Showing last {max_messages} of {len(all_messages)} messages[/dim]"
        )

    layout["messages"].update(
        Panel(
            messages_table,
            title="Messages & Tools",
            border_style="blue",
            padding=(1, 2),
        )
    )

    # Analysis panel showing current report
    if message_buffer.current_report:
        layout["analysis"].update(
            Panel(
                Markdown(message_buffer.current_report),
                title="Current Report",
                border_style="green",
                padding=(1, 2),
            )
        )
    else:
        layout["analysis"].update(
            Panel(
                "[italic]Waiting for analysis report...[/italic]",
                title="Current Report",
                border_style="green",
                padding=(1, 2),
            )
        )

    # Footer with statistics
    tool_calls_count = len(message_buffer.tool_calls)
    llm_calls_count = sum(
        1 for _, msg_type, _ in message_buffer.messages if msg_type == "Reasoning"
    )
    reports_count = sum(
        1 for content in message_buffer.report_sections.values() if content is not None
    )

    stats_table = Table(show_header=False, box=None, padding=(0, 2), expand=True)
    stats_table.add_column("Stats", justify="center")
    stats_table.add_row(
        f"Tool Calls: {tool_calls_count} | LLM Calls: {llm_calls_count} | Generated Reports: {reports_count}"
    )

    layout["footer"].update(Panel(stats_table, border_style="grey50"))


def get_user_selections(interactive: bool = False, use_defaults: bool = False):
    """Get all user selections before starting the analysis display."""
    from tradingagents.env_config import get_env_config

    # Get CLI configuration
    env_config = get_env_config()
    cli_config = env_config.get_cli_config()

    # Determine mode: use defaults unless specifically requested to be interactive
    should_use_defaults = (cli_config.get("cli_default_mode") == "auto" or use_defaults) and not interactive

    if should_use_defaults:
        console.print("[bold blue]🚀 Using default preferences - add --interactive to customize[/bold blue]\n")

    # Display ASCII art welcome message
    with open("./cli/static/welcome.txt", "r") as f:
        welcome_ascii = f.read()

    # Create welcome box content
    welcome_content = f"{welcome_ascii}\n"
    welcome_content += "[bold green]TradingAgents: Multi-Agents LLM Financial Trading Framework - CLI[/bold green]\n\n"
    welcome_content += "[bold]Workflow Steps:[/bold]\n"
    welcome_content += "I. Analyst Team → II. Research Team → III. Trader → IV. Risk Management → V. Portfolio Management\n\n"
    welcome_content += (
        "[dim]Built by [Tauric Research](https://github.com/TauricResearch)[/dim]"
    )

    # Create and center the welcome box
    welcome_box = Panel(
        welcome_content,
        border_style="green",
        padding=(1, 2),
        title="Welcome to TradingAgents",
        subtitle="Multi-Agents LLM Financial Trading Framework",
    )
    console.print(Align.center(welcome_box))
    console.print()  # Add a blank line after the welcome box

    # Create a boxed questionnaire for each step
    def create_question_box(title, prompt, default=None):
        box_content = f"[bold]{title}[/bold]\n"
        box_content += f"[dim]{prompt}[/dim]"
        if default:
            box_content += f"\n[dim]Default: {default}[/dim]"
        return Panel(box_content, border_style="blue", padding=(1, 2))

    # Step 1: Ticker symbol
    console.print(
        create_question_box(
            "Step 1: Ticker Symbol", "Enter the ticker symbol to analyze", "SPY"
        )
    )
    selected_ticker = get_ticker()

    # Step 2: Analysis date
    default_date = datetime.datetime.now().strftime("%Y-%m-%d")
    if should_use_defaults and cli_config.get("cli_auto_use_current_date", True):
        analysis_date = default_date
        console.print(f"[green]✓ Using current date: {analysis_date}[/green]")
    else:
        console.print(
            create_question_box(
                "Step 2: Analysis Date",
                "Enter the analysis date (YYYY-MM-DD)",
                default_date,
            )
        )
        analysis_date = get_analysis_date()

    # Step 3: Select analysts
    if should_use_defaults and cli_config.get("cli_auto_select_all_analysts", True):
        from cli.models import AnalystType
        selected_analysts = [analyst_type for _, analyst_type in ANALYST_ORDER]
        console.print(
            f"[green]✓ Using all analysts: {', '.join(analyst.value for analyst in selected_analysts)}[/green]"
        )
    else:
        console.print(
            create_question_box(
                "Step 3: Analysts Team", "Select your LLM analyst agents for the analysis"
            )
        )
        selected_analysts = select_analysts()
        console.print(
            f"[green]Selected analysts:[/green] {', '.join(analyst.value for analyst in selected_analysts)}"
        )

    # Step 4: Research depth
    if should_use_defaults:
        depth_map = {"shallow": 1, "medium": 3, "deep": 5}
        default_depth_name = cli_config.get("cli_default_research_depth", "deep")
        selected_research_depth = depth_map.get(default_depth_name, 5)
        console.print(f"[green]✓ Using research depth: {default_depth_name} ({selected_research_depth} rounds)[/green]")
    else:
        console.print(
            create_question_box(
                "Step 4: Research Depth", "Select your research depth level"
            )
        )
        selected_research_depth = select_research_depth()

    # Step 5: Bedrock Configuration (simplified - no provider selection needed)
    selected_llm_provider = "bedrock"
    backend_url = "aws-bedrock"
    console.print(f"[green]✓ Using AWS Bedrock with Claude models[/green]")

    # Step 6: Claude Model Selection (simplified for Bedrock-only)
    selected_shallow_thinker = cli_config.get("cli_default_shallow_thinker", "claude-3-5-sonnet")
    selected_deep_thinker = cli_config.get("cli_default_deep_thinker", "claude-sonnet-4")
    console.print(f"[green]✓ Using Claude models: {selected_shallow_thinker} (quick), {selected_deep_thinker} (deep)[/green]")

    return {
        "ticker": selected_ticker,
        "analysis_date": analysis_date,
        "analysts": selected_analysts,
        "research_depth": selected_research_depth,
        "llm_provider": selected_llm_provider.lower(),
        "backend_url": backend_url,
        "shallow_thinker": selected_shallow_thinker,
        "deep_thinker": selected_deep_thinker,
    }


def get_ticker():
    """Get ticker symbol from user input."""
    return typer.prompt("", default="SPY")


def get_analysis_date():
    """Get the analysis date from user input."""
    while True:
        date_str = typer.prompt(
            "", default=datetime.datetime.now().strftime("%Y-%m-%d")
        )
        try:
            # Validate date format and ensure it's not in the future
            analysis_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            if analysis_date.date() > datetime.datetime.now().date():
                console.print("[red]Error: Analysis date cannot be in the future[/red]")
                continue
            return date_str
        except ValueError:
            console.print(
                "[red]Error: Invalid date format. Please use YYYY-MM-DD[/red]"
            )


def display_complete_report(final_state):
    """Display the complete analysis report with team-based panels."""
    console.print("\n[bold green]Complete Analysis Report[/bold green]\n")

    # I. Analyst Team Reports
    analyst_reports = []

    # Market Analyst Report
    if final_state.get("market_report"):
        analyst_reports.append(
            Panel(
                Markdown(final_state["market_report"]),
                title="Market Analyst",
                border_style="blue",
                padding=(1, 2),
            )
        )

    # Social Analyst Report
    if final_state.get("sentiment_report"):
        analyst_reports.append(
            Panel(
                Markdown(final_state["sentiment_report"]),
                title="Social Analyst",
                border_style="blue",
                padding=(1, 2),
            )
        )

    # News Analyst Report
    if final_state.get("news_report"):
        analyst_reports.append(
            Panel(
                Markdown(final_state["news_report"]),
                title="News Analyst",
                border_style="blue",
                padding=(1, 2),
            )
        )

    # Fundamentals Analyst Report
    if final_state.get("fundamentals_report"):
        analyst_reports.append(
            Panel(
                Markdown(final_state["fundamentals_report"]),
                title="Fundamentals Analyst",
                border_style="blue",
                padding=(1, 2),
            )
        )

    if analyst_reports:
        console.print(
            Panel(
                Columns(analyst_reports, equal=True, expand=True),
                title="I. Analyst Team Reports",
                border_style="cyan",
                padding=(1, 2),
            )
        )

    # II. Research Team Reports
    if final_state.get("investment_debate_state"):
        research_reports = []
        debate_state = final_state["investment_debate_state"]

        # Bull Researcher Analysis
        if debate_state.get("bull_history"):
            research_reports.append(
                Panel(
                    Markdown(debate_state["bull_history"]),
                    title="Bull Researcher",
                    border_style="blue",
                    padding=(1, 2),
                )
            )

        # Bear Researcher Analysis
        if debate_state.get("bear_history"):
            research_reports.append(
                Panel(
                    Markdown(debate_state["bear_history"]),
                    title="Bear Researcher",
                    border_style="blue",
                    padding=(1, 2),
                )
            )

        # Research Manager Decision
        if debate_state.get("judge_decision"):
            research_reports.append(
                Panel(
                    Markdown(debate_state["judge_decision"]),
                    title="Research Manager",
                    border_style="blue",
                    padding=(1, 2),
                )
            )

        if research_reports:
            console.print(
                Panel(
                    Columns(research_reports, equal=True, expand=True),
                    title="II. Research Team Decision",
                    border_style="magenta",
                    padding=(1, 2),
                )
            )

    # III. Trading Team Reports
    if final_state.get("trader_investment_plan"):
        console.print(
            Panel(
                Panel(
                    Markdown(final_state["trader_investment_plan"]),
                    title="Trader",
                    border_style="blue",
                    padding=(1, 2),
                ),
                title="III. Trading Team Plan",
                border_style="yellow",
                padding=(1, 2),
            )
        )

    # IV. Risk Management Team Reports
    if final_state.get("risk_debate_state"):
        risk_reports = []
        risk_state = final_state["risk_debate_state"]

        # Aggressive (Risky) Analyst Analysis
        if risk_state.get("risky_history"):
            risk_reports.append(
                Panel(
                    Markdown(risk_state["risky_history"]),
                    title="Aggressive Analyst",
                    border_style="blue",
                    padding=(1, 2),
                )
            )

        # Conservative (Safe) Analyst Analysis
        if risk_state.get("safe_history"):
            risk_reports.append(
                Panel(
                    Markdown(risk_state["safe_history"]),
                    title="Conservative Analyst",
                    border_style="blue",
                    padding=(1, 2),
                )
            )

        # Neutral Analyst Analysis
        if risk_state.get("neutral_history"):
            risk_reports.append(
                Panel(
                    Markdown(risk_state["neutral_history"]),
                    title="Neutral Analyst",
                    border_style="blue",
                    padding=(1, 2),
                )
            )

        if risk_reports:
            console.print(
                Panel(
                    Columns(risk_reports, equal=True, expand=True),
                    title="IV. Risk Management Team Decision",
                    border_style="red",
                    padding=(1, 2),
                )
            )

        # V. Portfolio Manager Decision
        if risk_state.get("judge_decision"):
            console.print(
                Panel(
                    Panel(
                        Markdown(risk_state["judge_decision"]),
                        title="Portfolio Manager",
                        border_style="blue",
                        padding=(1, 2),
                    ),
                    title="V. Portfolio Manager Decision",
                    border_style="green",
                    padding=(1, 2),
                )
            )


def update_research_team_status(status):
    """Update status for all research team members and trader."""
    research_team = ["Bull Researcher", "Bear Researcher", "Research Manager", "Trader"]
    for agent in research_team:
        message_buffer.update_agent_status(agent, status)

def extract_content_string(content):
    """Extract string content from various message formats."""
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        # Handle Anthropic's list format
        text_parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get('type') == 'text':
                    text_parts.append(item.get('text', ''))
                elif item.get('type') == 'tool_use':
                    text_parts.append(f"[Tool: {item.get('name', 'unknown')}]")
            else:
                text_parts.append(str(item))
        return ' '.join(text_parts)
    else:
        return str(content)

def run_analysis(interactive: bool = False, use_defaults: bool = False):
    # First get all user selections
    selections = get_user_selections(interactive=interactive, use_defaults=use_defaults)

    # Create config with selected research depth
    config = DEFAULT_CONFIG.copy()
    config["max_debate_rounds"] = selections["research_depth"]
    config["max_risk_discuss_rounds"] = selections["research_depth"]
    config["quick_think_llm"] = selections["shallow_thinker"]
    config["deep_think_llm"] = selections["deep_thinker"]
    config["backend_url"] = selections["backend_url"]
    config["llm_provider"] = selections["llm_provider"].lower()

    # Initialize the graph
    graph = TradingAgentsGraph(
        [analyst.value for analyst in selections["analysts"]], config=config, debug=True
    )

    # Create result directory
    results_dir = Path(config["results_dir"]) / selections["ticker"] / selections["analysis_date"]
    results_dir.mkdir(parents=True, exist_ok=True)
    report_dir = results_dir / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    log_file = results_dir / "message_tool.log"
    log_file.touch(exist_ok=True)

    def save_message_decorator(obj, func_name):
        func = getattr(obj, func_name)
        @wraps(func)
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)
            timestamp, message_type, content = obj.messages[-1]
            content = content.replace("\n", " ")  # Replace newlines with spaces
            with open(log_file, "a") as f:
                f.write(f"{timestamp} [{message_type}] {content}\n")
        return wrapper
    
    def save_tool_call_decorator(obj, func_name):
        func = getattr(obj, func_name)
        @wraps(func)
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)
            timestamp, tool_name, args = obj.tool_calls[-1]
            args_str = ", ".join(f"{k}={v}" for k, v in args.items())
            with open(log_file, "a") as f:
                f.write(f"{timestamp} [Tool Call] {tool_name}({args_str})\n")
        return wrapper

    def save_report_section_decorator(obj, func_name):
        func = getattr(obj, func_name)
        @wraps(func)
        def wrapper(section_name, content):
            func(section_name, content)
            if section_name in obj.report_sections and obj.report_sections[section_name] is not None:
                content = obj.report_sections[section_name]
                if content:
                    file_name = f"{section_name}.md"
                    with open(report_dir / file_name, "w") as f:
                        f.write(content)
        return wrapper

    message_buffer.add_message = save_message_decorator(message_buffer, "add_message")
    message_buffer.add_tool_call = save_tool_call_decorator(message_buffer, "add_tool_call")
    message_buffer.update_report_section = save_report_section_decorator(message_buffer, "update_report_section")

    # Now start the display layout
    layout = create_layout()

    with Live(layout, refresh_per_second=4) as live:
        # Initial display
        update_display(layout)

        # Add initial messages
        message_buffer.add_message("System", f"Selected ticker: {selections['ticker']}")
        message_buffer.add_message(
            "System", f"Analysis date: {selections['analysis_date']}"
        )
        message_buffer.add_message(
            "System",
            f"Selected analysts: {', '.join(analyst.value for analyst in selections['analysts'])}",
        )
        update_display(layout)

        # Reset agent statuses
        for agent in message_buffer.agent_status:
            message_buffer.update_agent_status(agent, "pending")

        # Reset report sections
        for section in message_buffer.report_sections:
            message_buffer.report_sections[section] = None
        message_buffer.current_report = None
        message_buffer.final_report = None

        # Update agent status to in_progress for the first analyst
        first_analyst = f"{selections['analysts'][0].value.capitalize()} Analyst"
        message_buffer.update_agent_status(first_analyst, "in_progress")
        update_display(layout)

        # Create spinner text
        spinner_text = (
            f"Analyzing {selections['ticker']} on {selections['analysis_date']}..."
        )
        update_display(layout, spinner_text)

        # Initialize state and get graph args
        init_agent_state = graph.propagator.create_initial_state(
            selections["ticker"], selections["analysis_date"]
        )
        args = graph.propagator.get_graph_args()

        # Stream the analysis
        trace = []
        for chunk in graph.graph.stream(init_agent_state, **args):
            if len(chunk["messages"]) > 0:
                # Get the last message from the chunk
                last_message = chunk["messages"][-1]

                # Extract message content and type
                if hasattr(last_message, "content"):
                    content = extract_content_string(last_message.content)  # Use the helper function
                    msg_type = "Reasoning"
                else:
                    content = str(last_message)
                    msg_type = "System"

                # Add message to buffer
                message_buffer.add_message(msg_type, content)                

                # If it's a tool call, add it to tool calls
                if hasattr(last_message, "tool_calls"):
                    for tool_call in last_message.tool_calls:
                        # Handle both dictionary and object tool calls
                        if isinstance(tool_call, dict):
                            message_buffer.add_tool_call(
                                tool_call["name"], tool_call["args"]
                            )
                        else:
                            message_buffer.add_tool_call(tool_call.name, tool_call.args)

                # Update reports and agent status based on chunk content
                # Analyst Team Reports
                if "market_report" in chunk and chunk["market_report"]:
                    message_buffer.update_report_section(
                        "market_report", chunk["market_report"]
                    )
                    message_buffer.update_agent_status("Market Analyst", "completed")
                    # Set next analyst to in_progress
                    if "social" in selections["analysts"]:
                        message_buffer.update_agent_status(
                            "Social Analyst", "in_progress"
                        )

                if "sentiment_report" in chunk and chunk["sentiment_report"]:
                    message_buffer.update_report_section(
                        "sentiment_report", chunk["sentiment_report"]
                    )
                    message_buffer.update_agent_status("Social Analyst", "completed")
                    # Set next analyst to in_progress
                    if "news" in selections["analysts"]:
                        message_buffer.update_agent_status(
                            "News Analyst", "in_progress"
                        )

                if "news_report" in chunk and chunk["news_report"]:
                    message_buffer.update_report_section(
                        "news_report", chunk["news_report"]
                    )
                    message_buffer.update_agent_status("News Analyst", "completed")
                    # Set next analyst to in_progress
                    if "fundamentals" in selections["analysts"]:
                        message_buffer.update_agent_status(
                            "Fundamentals Analyst", "in_progress"
                        )

                if "fundamentals_report" in chunk and chunk["fundamentals_report"]:
                    message_buffer.update_report_section(
                        "fundamentals_report", chunk["fundamentals_report"]
                    )
                    message_buffer.update_agent_status(
                        "Fundamentals Analyst", "completed"
                    )
                    # Set all research team members to in_progress
                    update_research_team_status("in_progress")

                # Research Team - Handle Investment Debate State
                if (
                    "investment_debate_state" in chunk
                    and chunk["investment_debate_state"]
                ):
                    debate_state = chunk["investment_debate_state"]

                    # Update Bull Researcher status and report
                    if "bull_history" in debate_state and debate_state["bull_history"]:
                        # Keep all research team members in progress
                        update_research_team_status("in_progress")
                        # Extract latest bull response
                        bull_responses = debate_state["bull_history"].split("\n")
                        latest_bull = bull_responses[-1] if bull_responses else ""
                        if latest_bull:
                            message_buffer.add_message("Reasoning", latest_bull)
                            # Update research report with bull's latest analysis
                            message_buffer.update_report_section(
                                "investment_plan",
                                f"### Bull Researcher Analysis\n{latest_bull}",
                            )

                    # Update Bear Researcher status and report
                    if "bear_history" in debate_state and debate_state["bear_history"]:
                        # Keep all research team members in progress
                        update_research_team_status("in_progress")
                        # Extract latest bear response
                        bear_responses = debate_state["bear_history"].split("\n")
                        latest_bear = bear_responses[-1] if bear_responses else ""
                        if latest_bear:
                            message_buffer.add_message("Reasoning", latest_bear)
                            # Update research report with bear's latest analysis
                            message_buffer.update_report_section(
                                "investment_plan",
                                f"{message_buffer.report_sections['investment_plan']}\n\n### Bear Researcher Analysis\n{latest_bear}",
                            )

                    # Update Research Manager status and final decision
                    if (
                        "judge_decision" in debate_state
                        and debate_state["judge_decision"]
                    ):
                        # Keep all research team members in progress until final decision
                        update_research_team_status("in_progress")
                        message_buffer.add_message(
                            "Reasoning",
                            f"Research Manager: {debate_state['judge_decision']}",
                        )
                        # Update research report with final decision
                        message_buffer.update_report_section(
                            "investment_plan",
                            f"{message_buffer.report_sections['investment_plan']}\n\n### Research Manager Decision\n{debate_state['judge_decision']}",
                        )
                        # Mark all research team members as completed
                        update_research_team_status("completed")
                        # Set first risk analyst to in_progress
                        message_buffer.update_agent_status(
                            "Risky Analyst", "in_progress"
                        )

                # Trading Team
                if (
                    "trader_investment_plan" in chunk
                    and chunk["trader_investment_plan"]
                ):
                    message_buffer.update_report_section(
                        "trader_investment_plan", chunk["trader_investment_plan"]
                    )
                    # Set first risk analyst to in_progress
                    message_buffer.update_agent_status("Risky Analyst", "in_progress")

                # Risk Management Team - Handle Risk Debate State
                if "risk_debate_state" in chunk and chunk["risk_debate_state"]:
                    risk_state = chunk["risk_debate_state"]

                    # Update Risky Analyst status and report
                    if (
                        "current_risky_response" in risk_state
                        and risk_state["current_risky_response"]
                    ):
                        message_buffer.update_agent_status(
                            "Risky Analyst", "in_progress"
                        )
                        message_buffer.add_message(
                            "Reasoning",
                            f"Risky Analyst: {risk_state['current_risky_response']}",
                        )
                        # Update risk report with risky analyst's latest analysis only
                        message_buffer.update_report_section(
                            "final_trade_decision",
                            f"### Risky Analyst Analysis\n{risk_state['current_risky_response']}",
                        )

                    # Update Safe Analyst status and report
                    if (
                        "current_safe_response" in risk_state
                        and risk_state["current_safe_response"]
                    ):
                        message_buffer.update_agent_status(
                            "Safe Analyst", "in_progress"
                        )
                        message_buffer.add_message(
                            "Reasoning",
                            f"Safe Analyst: {risk_state['current_safe_response']}",
                        )
                        # Update risk report with safe analyst's latest analysis only
                        message_buffer.update_report_section(
                            "final_trade_decision",
                            f"### Safe Analyst Analysis\n{risk_state['current_safe_response']}",
                        )

                    # Update Neutral Analyst status and report
                    if (
                        "current_neutral_response" in risk_state
                        and risk_state["current_neutral_response"]
                    ):
                        message_buffer.update_agent_status(
                            "Neutral Analyst", "in_progress"
                        )
                        message_buffer.add_message(
                            "Reasoning",
                            f"Neutral Analyst: {risk_state['current_neutral_response']}",
                        )
                        # Update risk report with neutral analyst's latest analysis only
                        message_buffer.update_report_section(
                            "final_trade_decision",
                            f"### Neutral Analyst Analysis\n{risk_state['current_neutral_response']}",
                        )

                    # Update Portfolio Manager status and final decision
                    if "judge_decision" in risk_state and risk_state["judge_decision"]:
                        message_buffer.update_agent_status(
                            "Portfolio Manager", "in_progress"
                        )
                        message_buffer.add_message(
                            "Reasoning",
                            f"Portfolio Manager: {risk_state['judge_decision']}",
                        )
                        # Update risk report with final decision only
                        message_buffer.update_report_section(
                            "final_trade_decision",
                            f"### Portfolio Manager Decision\n{risk_state['judge_decision']}",
                        )
                        # Mark risk analysts as completed
                        message_buffer.update_agent_status("Risky Analyst", "completed")
                        message_buffer.update_agent_status("Safe Analyst", "completed")
                        message_buffer.update_agent_status(
                            "Neutral Analyst", "completed"
                        )
                        message_buffer.update_agent_status(
                            "Portfolio Manager", "completed"
                        )

                # Update the display
                update_display(layout)

            trace.append(chunk)

        # Get final state and decision
        final_state = trace[-1]
        decision = graph.process_signal(final_state["final_trade_decision"])

        # Update all agent statuses to completed
        for agent in message_buffer.agent_status:
            message_buffer.update_agent_status(agent, "completed")

        message_buffer.add_message(
            "Analysis", f"Completed analysis for {selections['analysis_date']}"
        )

        # Update final report sections
        for section in message_buffer.report_sections.keys():
            if section in final_state:
                message_buffer.update_report_section(section, final_state[section])

        # Display the complete final report
        display_complete_report(final_state)

        update_display(layout)


@app.command("analyze")
def analyze_ticker(
    symbol: str = typer.Argument(help="Stock ticker symbol to analyze (e.g., AAPL, TSLA)"),
    date: Optional[str] = typer.Option(
        None,
        "--date",
        "-d",
        help="Analysis date (YYYY-MM-DD), defaults to today"
    ),
    fast: bool = typer.Option(
        False,
        "--fast",
        "-f",
        help="Fast mode: skip debates for quicker analysis"
    ),
    output: str = typer.Option(
        "summary",
        "--output",
        "-o",
        help="Output format: 'summary', 'detailed', or 'decision'"
    )
):
    """Analyze a single stock ticker for trading decisions."""
    import datetime
    from tradingagents.graph.trading_graph import TradingAgentsGraph

    # Set analysis date
    if date is None:
        analysis_date = datetime.datetime.now().strftime("%Y-%m-%d")
    else:
        analysis_date = date

    # Create configuration for fast analysis if requested
    config = DEFAULT_CONFIG.copy()
    if fast:
        config["max_debate_rounds"] = 0
        config["max_risk_discuss_rounds"] = 0

    try:
        console.print(Panel(
            f"[bold blue]📊 Single Ticker Analysis[/bold blue]\n"
            f"🎯 Ticker: {symbol.upper()}\n"
            f"📅 Date: {analysis_date}\n"
            f"⚡ Mode: {'Fast' if fast else 'Full'} Analysis\n"
            f"📋 Output: {output.title()}",
            title="Ticker Analysis Starting",
            border_style="blue"
        ))

        # Initialize trading graph
        with console.status(f"[bold green]Analyzing {symbol.upper()}...") as status:
            graph = TradingAgentsGraph(config=config)

            status.update(f"[bold green]Running analysis for {symbol.upper()}...")
            final_state, decision = graph.propagate(symbol.upper(), analysis_date)

        # Display results based on output format
        if output == "decision":
            # Just the final decision
            console.print(Panel(
                f"[bold green]🎯 Final Decision: {decision}[/bold green]",
                title=f"{symbol.upper()} Trading Decision",
                border_style="green"
            ))

        elif output == "summary":
            # Summary with key points
            console.print(f"\n[bold cyan]📊 Analysis Summary for {symbol.upper()}[/bold cyan]\n")

            # Final Decision
            console.print(Panel(
                f"[bold green]🎯 Final Decision: {decision}[/bold green]",
                title="Trading Recommendation",
                border_style="green"
            ))

            # Key Reports (if available)
            reports = []
            if final_state.get("market_report"):
                reports.append(("Market Analysis", final_state["market_report"][:200] + "..."))
            if final_state.get("sentiment_report"):
                reports.append(("Social Sentiment", final_state["sentiment_report"][:200] + "..."))
            if final_state.get("news_report"):
                reports.append(("News Analysis", final_state["news_report"][:200] + "..."))
            if final_state.get("final_trade_decision"):
                reports.append(("Final Reasoning", final_state["final_trade_decision"][:300] + "..."))

            if reports:
                for title, content in reports:
                    console.print(Panel(
                        content,
                        title=f"📋 {title}",
                        border_style="cyan",
                        padding=(1, 2)
                    ))

        else:  # detailed
            # Full detailed output (same as original analyze command)
            display_complete_report(final_state)

        console.print(f"\n[green]✅ Analysis completed for {symbol.upper()} on {analysis_date}[/green]")

    except Exception as e:
        console.print(f"[red]❌ Analysis failed for {symbol.upper()}: {e}[/red]")
        raise typer.Exit(1)


@app.command("batch")
def batch_analysis(
    portfolio_file: str = typer.Option(
        "portfolio.json",
        "--file",
        "-f",
        help="Portfolio configuration file path"
    ),
    trade_date: Optional[str] = typer.Option(
        None,
        "--date",
        "-d",
        help="Analysis date (YYYY-MM-DD), defaults to today"
    ),
    output: str = typer.Option(
        "summary",
        "--output",
        "-o",
        help="Output format: 'summary' (default), 'detailed', or 'decisions'"
    ),
    parallel: bool = typer.Option(
        True,
        "--parallel/--sequential",
        help="Run individual analyses in parallel (default: True)"
    ),
    max_workers: int = typer.Option(
        4,
        "--max-workers",
        help="Maximum parallel workers (default: 4)"
    )
):
    """Batch analysis on multiple stocks from portfolio file."""
    import datetime
    from tradingagents.agents.portfolio_batch import batch_analyze_portfolio

    try:
        # Set default date if not provided
        if not trade_date:
            trade_date = datetime.datetime.now().strftime("%Y-%m-%d")

        console.print(Panel(
            f"[bold blue]📊 Batch Stock Analysis[/bold blue]\n"
            f"📁 File: {portfolio_file}\n"
            f"📅 Date: {trade_date}\n"
            f"⚡ Workers: {max_workers}",
            title="Batch Analysis Starting",
            border_style="blue"
        ))

        # Initialize trading graph and run simplified batch analysis
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        graph = TradingAgentsGraph(config=DEFAULT_CONFIG)

        results = batch_analyze_portfolio(
            graph,
            portfolio_file=portfolio_file,
            date=trade_date,
            max_workers=max_workers,
            output_format=output
        )

        console.print(f"\n[bold green]✅ {results['summary']}[/bold green]")

    except FileNotFoundError:
        console.print(f"[red]Portfolio file '{portfolio_file}' not found.[/red]")
        console.print("[yellow]Expected format: {'positions': [{'ticker': 'AAPL', 'shares': 100, 'price_bought': 150.00}]}[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise typer.Exit(1)


def display_analysis_summary(report: Dict[str, Any]):
    """Display analysis completion summary with error reporting."""
    # Count successful vs failed analyses
    total_tickers = 0
    successful_tickers = 0
    failed_tickers = []

    for ticker, analysis in report.get("detailed_stock_analysis", {}).items():
        total_tickers += 1
        if "error" in analysis:
            failed_tickers.append(ticker)
        else:
            successful_tickers += 1

    # Display summary
    if failed_tickers:
        console.print(Panel(
            f"[bold yellow]⚠️  Analysis Summary[/bold yellow]\n\n"
            f"✅ Successful: {successful_tickers}/{total_tickers} stocks\n"
            f"❌ Failed: {len(failed_tickers)} stocks\n"
            f"📛 Failed tickers: {', '.join(failed_tickers)}\n\n"
            f"[dim]Continuing with partial results...[/dim]",
            title="Analysis Status",
            border_style="yellow"
        ))
    else:
        console.print(Panel(
            f"[bold green]✅ Analysis Summary[/bold green]\n\n"
            f"Successfully analyzed all {total_tickers} stocks!\n"
            f"📊 Ready for trading recommendations",
            title="Analysis Complete",
            border_style="green"
        ))


def display_portfolio_summary(report: Dict[str, Any]):
    """Display portfolio summary report."""
    summary = report["portfolio_summary"]
    risk = report["risk_assessment"]
    actions = report["action_summary"]

    # Portfolio Overview
    console.print(Panel(
        f"[bold green]📊 Portfolio: {summary['name']}[/bold green]\n\n"
        f"💰 Total Value: ${summary['total_value']:,.2f}\n"
        f"💵 Cash: ${summary['cash_available']:,.2f} ({risk['cash_percentage']:.1f}%)\n"
        f"📈 Invested: ${summary['invested_value']:,.2f}\n"
        f"📦 Positions: {summary['num_positions']} stocks\n"
        f"👁️  Watchlist: {summary['num_watchlist']} stocks\n\n"
        f"⚠️  Risk Score: {risk['overall_risk_score']:.1f}/10",
        title="Portfolio Summary",
        border_style="green"
    ))

    # Risk Alerts
    if risk["risk_alerts"]:
        alerts_text = "\n".join([f"• {alert}" for alert in risk["risk_alerts"][:5]])
        console.print(Panel(
            alerts_text,
            title="⚠️  Risk Alerts",
            border_style="yellow"
        ))

    # Action Summary
    if actions["total_actions"] > 0:
        action_text = f"[bold]Total Actions: {actions['total_actions']}[/bold]\n"
        action_text += f"High Priority: {actions['high_priority']}\n\n"

        for i, action in enumerate(actions["actions"][:5], 1):
            action_text += f"{i}. {action['ticker']}: {action['action']} {action['shares']} shares\n"
            action_text += f"   {action['reasoning'][:60]}...\n\n"

        console.print(Panel(
            action_text,
            title="💡 Priority Actions",
            border_style="blue"
        ))


def display_portfolio_detailed(report: Dict[str, Any]):
    """Display detailed portfolio analysis report."""
    # Show summary first
    display_portfolio_summary(report)

    # Position Analysis
    if report["position_analysis"]:
        console.print("\n")
        positions_table = Table(title="📈 Position Analysis & Recommendations")
        positions_table.add_column("Ticker", style="cyan")
        positions_table.add_column("Shares", justify="right")
        positions_table.add_column("Value", justify="right")
        positions_table.add_column("Weight", justify="right")
        positions_table.add_column("P&L%", justify="right")
        positions_table.add_column("Recommendation", style="bold")

        for pos in report["position_analysis"]:
            # Check if this position had analysis errors
            ticker = pos["ticker"]
            analysis = report.get("detailed_stock_analysis", {}).get(ticker, {})
            has_error = "error" in analysis

            if has_error:
                # Show error status for failed analyses
                positions_table.add_row(
                    f"[red]{ticker}[/red]",
                    str(pos["current_shares"]),
                    f"${pos['current_value']:,.0f}",
                    f"{pos['weight_pct']:.1f}%",
                    f"[red]N/A (Error)[/red]",
                    "[yellow]HOLD (Error)[/yellow]"
                )
            else:
                # Normal display for successful analyses
                pnl_style = "green" if pos["pnl_pct"] > 0 else "red"
                action_style = "red" if pos["action"] == "SELL" else "green" if pos["action"] in ["BUY", "ADD"] else "yellow"

                positions_table.add_row(
                    pos["ticker"],
                    str(pos["current_shares"]),
                    f"${pos['current_value']:,.0f}",
                    f"{pos['weight_pct']:.1f}%",
                    f"[{pnl_style}]{pos['pnl_pct']:+.1f}%[/{pnl_style}]",
                    f"[{action_style}]{pos['action']}[/{action_style}]"
                )

        console.print(positions_table)

    # Watchlist Opportunities
    if report["watchlist_opportunities"]:
        console.print("\n")
        watchlist_table = Table(title="🎯 New Opportunities (Watchlist)")
        watchlist_table.add_column("Ticker", style="cyan")
        watchlist_table.add_column("Price", justify="right")
        watchlist_table.add_column("Target%", justify="right")
        watchlist_table.add_column("Shares", justify="right")
        watchlist_table.add_column("Cost", justify="right")
        watchlist_table.add_column("Decision", style="bold")

        for item in report["watchlist_opportunities"]:
            decision_style = "green" if item["agent_decision"] == "BUY" else "yellow"

            watchlist_table.add_row(
                item["ticker"],
                f"${item['current_price']:.2f}",
                f"{item['target_allocation_pct']:.1f}%",
                str(item["recommended_shares"]),
                f"${item['estimated_cost']:,.0f}",
                f"[{decision_style}]{item['agent_decision']}[/{decision_style}]"
            )

        console.print(watchlist_table)

    # Sector Allocation
    console.print("\n")
    sector_table = Table(title="🏭 Sector Allocation")
    sector_table.add_column("Sector", style="cyan")
    sector_table.add_column("Allocation", justify="right")

    for sector, allocation in report["risk_assessment"]["sector_allocations"].items():
        color = "red" if allocation > 40 else "yellow" if allocation > 25 else "green"
        sector_table.add_row(sector, f"[{color}]{allocation:.1f}%[/{color}]")

    console.print(sector_table)

    console.print(f"\n[dim]Report generated: {report['report_date']}[/dim]")


if __name__ == "__main__":
    app()
