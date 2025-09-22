"""
Pharmacy SMS Chatbot - Interactive CLI Application

Interactive command-line interface for the pharmacy chatbot system.
Users can chat with the bot directly through the terminal.
"""

import typer
from typing_extensions import Annotated
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import env
from src.core.models import ConversationContext
from src.core.chatbot import PharmacyChatbot, ChatbotError
from src.core.pharmacy_service import find_pharmacy_by_phone, initialize_conversation
from src.api.pharmacy.client import PharmacyClient, PharmacyAPIError
from src.api.follow_up_actions import (
    send_pharmacy_welcome_email,
    send_lead_follow_up_email,
    schedule_callback,
    create_crm_entry
)

# CLI Message Constants
WELCOME_PANEL_TITLE = "Pharmacy Chatbot"
WELCOME_PANEL_CONTENT = (
    "[bold blue]🏥 Welcome to Pharmesol Interactive Chat[/bold blue]\n"
    "[dim]Phone: {phone}[/dim]\n"
    "[dim]Type your messages and press Enter. Type 'quit', 'exit', or 'bye' to end.[/dim]"
)

SESSION_COMPLETE_TITLE = "Session Complete"
SESSION_COMPLETE_CONTENT = (
    "[bold green]✅ Chat session completed![/bold green]\n"
    "[dim]Conversation with {caller_name} has ended.[/dim]"
)

DEMO_PANEL_TITLE = "Demo Mode"
DEMO_PANEL_CONTENT = "[bold blue]🎭 Pharmacy Chatbot Demo Scenarios[/bold blue]"

ERROR_NO_PHARMACY_DATA = "[red]Cannot proceed without pharmacy data.[/red]"
ERROR_LOAD_PHARMACY_DATA = "[red]❌ Failed to load pharmacy data: {error}[/red]"
ERROR_INIT_CHATBOT = "[red]❌ Failed to initialize chatbot: {error}[/red]"

WARNING_NO_OPENAI = "[yellow]⚠️  No OpenAI API key found. Using fallback responses.[/yellow]"
WARNING_CHAT_ENDED = "[yellow]Chat session ended.[/yellow]"
WARNING_RUNNING_SCENARIOS = "[yellow]Running all demo scenarios via pytest...[/yellow]"
WARNING_RUNNING_SCENARIO = "[yellow]Running {scenario} scenario...[/yellow]"

INFO_EXECUTING_ACTIONS = "[bold blue]🎯 Executing follow-up actions...[/bold blue]"
INFO_RUNNING_TESTS = "[bold blue]🧪 Running Test Suite[/bold blue]"

BOT_GOODBYE = "🤖 [bold green]Bot:[/bold green] Thank you for chatting with us! Have a great day!"
BOT_PREFIX = "🤖 [bold green]Bot:[/bold green]"
USER_PREFIX = "👤 You"

FALLBACK_GREETING_RETURNING = """Hello {pharmacy_name}! 👋

Great to hear from you again. I see you're calling from {location} with {total_rx_volume} total prescriptions.

How can {company_name} help you today?"""

FALLBACK_GREETING_NEW = """Hello! 👋 Thank you for contacting {company_name}.

I don't recognize this number - are you a new pharmacy looking to learn about our services?

{company_name} specializes in supporting high-volume pharmacies with comprehensive solutions. I'd love to learn more about your pharmacy!"""

FALLBACK_RESPONSES = [
    "That's great to hear! Tell me more about your pharmacy.",
    "I understand. {company_name} specializes in helping high-volume pharmacies like yours.",
    "Perfect! I'd love to follow up with you. Would you prefer email or a phone call?",
    "Thank you for that information. Our team will be in touch soon!",
    "I appreciate you sharing that with me. Is there anything else I can help you with today?"
]

EXIT_COMMANDS = ['quit', 'exit', 'bye', 'goodbye']

app = typer.Typer(
    name="pharmacy-chatbot",
    help="🏥 Pharmacy SMS Chatbot - Interactive CLI for pharmacy conversations",
    rich_markup_mode="rich"
)
console = Console()


def load_pharmacy_data():
    try:
        client = PharmacyClient(env.PHARMACY_API_URL)
        return client.fetch_all_pharmacies_sync()
    except PharmacyAPIError as e:
        console.print(ERROR_LOAD_PHARMACY_DATA.format(error=e))
        return []


def initialize_chatbot():
    if not env.OPENAI_API_KEY:
        console.print(WARNING_NO_OPENAI)
        return None
    
    try:
        return PharmacyChatbot()
    except ChatbotError as e:
        console.print(ERROR_INIT_CHATBOT.format(error=e))
        return None


def execute_follow_up_actions(context: ConversationContext):
    if context.is_returning_customer and context.pharmacy:
        pharmacy = context.pharmacy
        
        if pharmacy.email:
            send_pharmacy_welcome_email(pharmacy)
        
        schedule_callback(
            pharmacy.phone,
            notes=f"Follow-up call for {pharmacy.name} - discussed support needs"
        )
    
    elif context.new_lead and context.new_lead.is_complete:
        lead = context.new_lead
        
        send_lead_follow_up_email(lead)
        create_crm_entry(lead)
        schedule_callback(
            lead.phone,
            notes=f"New lead follow-up: {lead.name or 'Unknown pharmacy'}"
        )


@app.command()
def chat(
    phone: Annotated[str, typer.Option("--phone", "-p", help="Your pharmacy's phone number")] = "+1-555-DEMO-CHAT"
):
    """
    🗣️ Start an interactive chat session with the pharmacy chatbot.
    
    The bot will recognize your pharmacy if the phone number is in our system,
    or treat you as a new lead if it's unknown.
    """
    console.print(Panel.fit(
        WELCOME_PANEL_CONTENT.format(phone=phone),
        title=WELCOME_PANEL_TITLE
    ))
    
    pharmacies = load_pharmacy_data()
    if not pharmacies:
        console.print(ERROR_NO_PHARMACY_DATA)
        raise typer.Exit(1)
    
    chatbot = initialize_chatbot()
    
    pharmacy = find_pharmacy_by_phone(pharmacies, phone)
    context = initialize_conversation(phone, pharmacy)
    
    greeting = chatbot.generate_greeting(context) if chatbot else get_fallback_greeting(context)
    console.print(f"\n{BOT_PREFIX} {greeting}")
    
    while True:
        try:
            user_input = typer.prompt(f"\n{USER_PREFIX}")
            
            if user_input.lower() in EXIT_COMMANDS:
                console.print(f"\n{BOT_GOODBYE}")
                break
            
            if chatbot:
                response = chatbot.process_user_message(context, user_input)
            else:
                response = get_fallback_response(context, user_input)
            
            console.print(f"\n{BOT_PREFIX} {response}")
            
        except (KeyboardInterrupt, EOFError):
            console.print(f"\n\n{WARNING_CHAT_ENDED}")
            break
    
    console.print(f"\n{INFO_EXECUTING_ACTIONS}")
    execute_follow_up_actions(context)
    
    console.print(Panel.fit(
        SESSION_COMPLETE_CONTENT.format(caller_name=context.caller_name),
        title=SESSION_COMPLETE_TITLE
    ))


@app.command()
def demo(
    scenario: Annotated[str, typer.Option("--scenario", "-s", help="Demo scenario to run")] = "all"
):
    """
    🎭 Run predefined demo scenarios to showcase chatbot capabilities.
    
    Available scenarios: returning, new-lead, high-volume, all
    """
    console.print(Panel.fit(
        DEMO_PANEL_CONTENT,
        title=DEMO_PANEL_TITLE
    ))
    
    if scenario == "all":
        console.print(WARNING_RUNNING_SCENARIOS)
        import subprocess
        result = subprocess.run([
            "pytest", "tests/test_demo_scenarios.py", "-k", "test_complete_demo_flow", "-v", "-s"
        ], env={"PYTHONPATH": "/home/avillia/projects/python/pharmacy-chat-bot"})
        raise typer.Exit(result.returncode)
    
    console.print(WARNING_RUNNING_SCENARIO.format(scenario=scenario))
    console.print("Demo scenarios are available through pytest:")
    console.print("pytest tests/test_demo_scenarios.py -v")


@app.command()
def test():
    """
    🧪 Run the test suite to validate system functionality.
    """
    console.print(INFO_RUNNING_TESTS)
    console.print("Available test commands:")
    console.print("  • All tests: [bold]pytest tests/ -v[/bold]")
    console.print("  • Demo scenarios: [bold]pytest tests/test_demo_scenarios.py -v[/bold]")
    console.print("  • PromptManager: [bold]pytest tests/test_prompt_manager.py -v[/bold]")
    console.print("  • Follow-up actions: [bold]pytest tests/test_follow_up_actions.py -v[/bold]")


def get_fallback_greeting(context: ConversationContext) -> str:
    if context.is_returning_customer and context.pharmacy:
        pharmacy = context.pharmacy
        return FALLBACK_GREETING_RETURNING.format(
            pharmacy_name=pharmacy.name,
            location=pharmacy.location,
            total_rx_volume=pharmacy.total_rx_volume,
            company_name=env.COMPANY_NAME
        )
    else:
        return FALLBACK_GREETING_NEW.format(company_name=env.COMPANY_NAME)


def get_fallback_response(context: ConversationContext, message: str) -> str:
    responses = [
        FALLBACK_RESPONSES[0],
        FALLBACK_RESPONSES[1].format(company_name=env.COMPANY_NAME),
        FALLBACK_RESPONSES[2],
        FALLBACK_RESPONSES[3],
        FALLBACK_RESPONSES[4]
    ]
    
    message_count = len([m for m in context.messages if m.startswith("User:")])
    return responses[min(message_count - 1, len(responses) - 1)]


if __name__ == "__main__":
    app()