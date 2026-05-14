import os
from dotenv import load_dotenv
from crewai import Agent

# Load environment variables from .env file
load_dotenv()

# Ensure GROQ_API_KEY is available
if "GROQ_API_KEY" not in os.environ:
    raise ValueError("GROQ_API_KEY not found in environment variables. Please set it in your .env file.")

predictive_agent = Agent(
    role="Universal AI Inventory Data Analyst",
    goal="Adaptively read any shop's CSV data schema with pre-calculated system metrics, and predict top low-stock and high-trend items.",
    backstory="""
    You are an elite data scientist and supply chain AI. You have been trained to handle any arbitrary dataset 
    from any shop or e-commerce platform. You look at pre-calculated REORDER POINTS and SYSTEM PRIORITY to output exact lists.
    """,
    llm="groq/llama-3.3-70b-versatile",
    verbose=False
)

strategist_agent = Agent(
    role="Supply Chain Strategist & Supplier Negotiator",
    goal=(
        "Review the Analyst's report. Identify Critical and High priority items. "
        "For each item, confirm the exact Reorder_Qty and When_To_Reorder values. "
        "Rank suppliers into TIER 1 / TIER 2 / TIER 3 based on urgency. "
        "Append a section titled '### 🚚 Emergency Shipping & Logistics Plan' with "
        "a cost-benefit analysis of Standard vs Express shipping for critical items, "
        "and supplier contact recommendations per tier."
    ),
    backstory="""
    You are a veteran Supply Chain Director with 20 years of experience negotiating
    with global suppliers. You specialize in emergency restocking scenarios, supplier
    relationship management, and cost-optimized logistics decisions. You take the
    pre-calculated Reorder_Qty and When_To_Reorder values as ground truth and build
    actionable supplier-level procurement plans around them. You know exactly which
    supplier to call first, what quantity to order, and whether to use express or
    standard shipping based on the Days_Until_Stockout metric.
    """,
    llm="groq/llama-3.3-70b-versatile",
    verbose=False
)
