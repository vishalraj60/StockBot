import os
import sys
import csv
from crewai import Task, Crew
from universal_csv_agent import predictive_agent, strategist_agent

def calculate_inventory_metrics(data_sample):
    if not data_sample: return data_sample
    
    # Try to find columns
    keys = list(data_sample[0].keys())
    stock_col    = next((k for k in keys if any(w in k.lower() for w in ['stock', 'qty', 'quantity', 'inventory', 'remaining'])), None)

    # Detect weekly vs daily sales columns separately
    weekly_col   = next((k for k in keys if 'week' in k.lower() and any(w in k.lower() for w in ['sales', 'sold', 'demand', 'velocity'])), None)
    sales_col    = next((k for k in keys if any(w in k.lower() for w in ['sales', 'sold', 'demand', 'velocity'])), None)
    rating_col   = next((k for k in keys if any(w in k.lower() for w in ['rating', 'score', 'stars', 'review'])), None)
    supplier_col = next((k for k in keys if any(w in k.lower() for w in ['supplier', 'vendor', 'brand', 'manufacturer', 'source'])), None)

    LEAD_TIME_DAYS = 7   # default lead time in days
    REORDER_COVER  = 14  # how many extra days of stock to order
    IS_WEEKLY      = weekly_col is not None  # flag for weekly normalization
    active_sales_col = weekly_col if IS_WEEKLY else sales_col

    for row in data_sample:
        try:
            # --- Parse stock & daily sales ---
            stock_val = str(row[stock_col]).replace(',', '') if stock_col and row.get(stock_col) else '0'
            stock = float(''.join(c for c in stock_val if c.isdigit() or c == '.') or 0)

            raw_sales_val = str(row[active_sales_col]).replace(',', '') if active_sales_col and row.get(active_sales_col) else '5'
            raw_sales = float(''.join(c for c in raw_sales_val if c.isdigit() or c == '.') or 5.0)
            # Normalize weekly → daily
            sales = raw_sales / 7.0 if IS_WEEKLY else raw_sales
            if sales == 0:
                sales = 1.0  # avoid division-by-zero

            # --- Rating ---
            rating = 0.0
            if rating_col and row.get(rating_col):
                try:
                    rating = float(str(row[rating_col]).replace(',', '').strip())
                except ValueError:
                    rating = 0.0

            # --- Core Restock Formulas ---
            safety_stock    = sales * 0.20                          # 20% buffer
            reorder_point   = (sales * LEAD_TIME_DAYS) + safety_stock
            target_stock    = reorder_point + (sales * REORDER_COVER)
            reorder_qty     = max(0, round(target_stock - stock))
            days_until_out  = round(stock / sales) if stock > 0 else 0

            # When to reorder: how many days before we hit the reorder point
            days_to_reorder = round((stock - reorder_point) / sales) if stock > reorder_point else 0
            when_label      = "Reorder NOW" if days_to_reorder <= 0 else f"Reorder in {days_to_reorder} day(s)"

            # --- Priority ---
            if stock <= 0:
                priority = "CRITICAL"
            elif stock < reorder_point:
                priority = "HIGH"
            elif stock < reorder_point * 1.5:
                priority = "MEDIUM"
            else:
                priority = "LOW"

            # --- Supplier ---
            supplier = str(row.get(supplier_col, 'Unknown')).strip() if supplier_col else 'Unknown'

            row['System_Priority']      = priority
            row['Supplier']             = supplier
            row['Reorder_Point']        = round(reorder_point, 1)
            row['Reorder_Qty']          = reorder_qty
            row['Days_Until_Stockout']  = days_until_out
            row['Daily_Sales_Used']     = round(sales, 2)  # always show normalised daily figure
            row['When_To_Reorder']      = when_label
            row['Reorder_Point_Formula'] = (
                f"({'Weekly' if IS_WEEKLY else 'Daily'} {round(raw_sales,1)} "
                f"÷ {'7 = ' + str(round(sales,2)) + ' daily' if IS_WEEKLY else 'daily'}) "
                f"× {LEAD_TIME_DAYS}d + {round(safety_stock,1)} safety "
                f"= {round(reorder_point,1)} | Order {reorder_qty} units ({when_label})"
            )
            # --- Trend Score (sales velocity + rating weighted blend) ---
            # Normalise sales to 0-100 scale using a soft cap of 50 daily units
            sales_score  = min(sales / 50.0, 1.0) * 70   # 70% weight
            rating_score = (rating / 5.0) * 30 if rating > 0 else 0  # 30% weight
            row['Trend_Score'] = round(sales_score + rating_score, 1)
            row['Rating_Used']  = rating if rating > 0 else 'N/A'
        except Exception:
            row['System_Priority']     = "UNKNOWN"
            row['Reorder_Qty']         = 'N/A'
            row['When_To_Reorder']     = 'N/A'
            row['Days_Until_Stockout'] = 'N/A'
            row['Supplier']            = 'Unknown'
            row['Trend_Score']         = 0
            
    # --- Rank all rows by Trend_Score descending ---
    try:
        scored = [r for r in data_sample if isinstance(r.get('Trend_Score'), (int, float))]
        scored.sort(key=lambda r: r['Trend_Score'], reverse=True)
        for i, r in enumerate(scored, start=1):
            r['Trend_Rank'] = i  # 1 = hottest trend
    except Exception:
        pass

    return data_sample

def analyze_csv_file(csv_path: str) -> str:
    print("="*60)
    print(f"🌍 UNIVERSAL CSV PREDICTOR: {csv_path}")
    print("="*60)

    try:
        with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            columns = reader.fieldnames if reader.fieldnames else []
            data_sample = []
            total_rows = 0
            # Exclude massive text columns to save huge amounts of tokens
            ignore_keywords = ['url', 'link', 'image', 'picture', 'desc', 'detail', 'about', 'spec', 'review', 'comment', 'breadcrumb']
            keep_columns = [col for col in columns if not any(keyword in str(col).lower() for keyword in ignore_keywords)]
            if not keep_columns:
                keep_columns = columns

            for row in reader:
                total_rows += 1
                # Hard limit reduced to 10 to guarantee we stay completely under the 12000 token TPM limit
                if len(data_sample) < 10:  
                    # Extract only efficient columns and strictly truncate values to 20 chars max
                    trimmed_row = {k: (str(row[k])[:20] + '...' if row[k] and len(str(row[k])) > 20 else row[k]) for k in keep_columns}
                    data_sample.append(trimmed_row)
    except Exception as e:
        error_msg = f"❌ Failed to load CSV '{csv_path}': {str(e)}"
        print(error_msg)
        return error_msg, []
        
    data_sample = calculate_inventory_metrics(data_sample)
    
    task_description = f"""
    The user has provided a CSV file representing shop data.
    Total Products (Rows): {total_rows}
    Available Columns/Features: {columns}

    Here is a small sample of the data (up to 10 rows). Pre-calculated fields included:
    - System_Priority       : CRITICAL / HIGH / MEDIUM / LOW
    - Supplier              : detected from the CSV automatically
    - Reorder_Qty           : how many units to order right now
    - When_To_Reorder       : "Reorder NOW" or "Reorder in N day(s)"
    - Days_Until_Stockout   : days of stock remaining
    - Trend_Score           : 0–100 score (70% sales velocity + 30% rating); HIGHER = hotter trend
    - Trend_Rank            : 1 = hottest trend seller in the dataset
    - Reorder_Point_Formula : full formula trace

    Data Sample:
    {data_sample}

    YOUR GOAL — produce a Markdown report with EXACTLY these sections in order:

    ### 🚨 Critical / High Priority (Action Required)
    List ONLY items with CRITICAL or HIGH System_Priority.
    For EACH item show: Product Name | Priority | Current Stock | Days Until Stockout | Reorder Now.

    ### 🚀 High Trend Sellers
    Use the pre-calculated `Trend_Score` and `Trend_Rank` fields ONLY. Do NOT guess.
    List the top 5 items sorted by Trend_Rank (lowest number = hottest).
    For EACH item show: Trend_Rank | Product Name | Trend_Score | Daily Sales | Rating (if available) | Brief reason why it is trending.

    ### 🛒 Restock Recommendation Engine
    This is the most important section. For EVERY item that needs restocking (CRITICAL or HIGH priority):
    - **How much to reorder**: Use the pre-calculated `Reorder_Qty` field exactly.
    - **When to reorder**: Use the pre-calculated `When_To_Reorder` field exactly.
    - **Supplier Priority Ranking**: Group items by their `Supplier` column value.
      Rank suppliers from highest urgency to lowest based on the severity of their items:
        1. 🔴 TIER 1 — Suppliers with CRITICAL items (contact immediately)
        2. 🟠 TIER 2 — Suppliers with HIGH items (contact within 24 hours)
        3. 🟡 TIER 3 — Suppliers with MEDIUM items (schedule reorder this week)
      For each supplier tier, list: Supplier Name | Items to Reorder | Total Units to Order | Recommended Action.

    ### 📊 Comprehensive Explanation
    Explain the formula logic:
    - Reorder Point = (Daily Sales × Lead Time) + Safety Stock
    - Reorder Quantity = (Reorder Point + 14-day cover) - Current Stock
    - Days Until Stockout = Current Stock / Daily Sales
    Explain how these drove your categorization.

    Format your output cleanly in Markdown. Be precise with numbers — use the pre-calculated values from the data.
    """

    prediction_task = Task(
        description=task_description,
        agent=predictive_agent,
        expected_output="A structured markdown report identifying the top low-stock/high-trend items, along with an explanation of CSV semantics."
    )

    strategy_task = Task(
        description="""
        Review the outcome of the Data Analyst, specifically the 🚨 Critical / High Priority items
        and the 🛒 Restock Recommendation Engine section.

        Your job is to append ONE new section at the bottom of the report:

        ### 🚚 Emergency Shipping & Logistics Plan

        For each CRITICAL and HIGH priority item identified by the Analyst:
        1. Confirm the exact `Reorder_Qty` and `When_To_Reorder` values from the data.
        2. Based on `Days_Until_Stockout`:
           - 0–3 days → Recommend Express Shipping (justify the cost to prevent lost revenue).
           - 4–7 days → Recommend Priority Shipping.
           - 8+ days  → Standard Shipping is acceptable.
        3. Group your recommendations by Supplier Tier:
           - 🔴 TIER 1 Suppliers (CRITICAL items): Provide an immediate action script/message to send.
           - 🟠 TIER 2 Suppliers (HIGH items): Schedule a call within 24 hours.
           - 🟡 TIER 3 Suppliers (MEDIUM items): Add to this week's procurement plan.

        Do NOT repeat the Analyst's priority lists. Only add this new Logistics section.
        """,
        agent=strategist_agent,
        expected_output="The final markdown report with the analyst's findings PLUS the 🚚 Emergency Shipping & Logistics Plan section grouped by Supplier Tier."
    )

    crew = Crew(
        agents=[predictive_agent, strategist_agent],
        tasks=[prediction_task, strategy_task],
        verbose=False
    )

    print("🤖 Agent is analyzing the data schema and predicting trends...\n")
    try:
        # result might be a CrewOutput object. convert cleanly to str.
        result = crew.kickoff()
        output_data = str(result)
        print("\n" + "="*60)
        print("🎯 AI PREDICTION RESULTS:")
        print("="*60)
        print(output_data)
        
        # Save output to a file (optional but helpful)
        output_filename = "universal_prediction_report.md"
        with open(output_filename, 'w') as f:
            f.write(f"# Universal Prediction Report for {os.path.basename(csv_path)}\n\n")
            f.write(output_data)
            
        print(f"\n✅ Report successfully saved to '{output_filename}'")
        return output_data, data_sample
    except Exception as e:
        error_str = str(e)
        print(f"❌ AI Analysis Error: {error_str}")
        return f"**AI Analysis Error**: {error_str}", []

def ask_advisor(message: str, context_data: list) -> str:
    from langchain_groq import ChatGroq
    from langchain.agents import AgentExecutor, create_tool_calling_agent
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_community.tools import DuckDuckGoSearchResults
    import json
    
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "⚠️ Error: Groq API Key not found. Please set it in Settings."
        
    try:
        # Initialize the ChatGroq model
        chat = ChatGroq(temperature=0.2, groq_api_key=api_key, model_name="llama-3.3-70b-versatile")
        
        # Initialize the search tool
        search = DuckDuckGoSearchResults()
        tools = [search]
        
        # Prepare context data (limit to top 50 items to save tokens)
        safe_context = context_data[:50] if context_data else []
        context_str = json.dumps(safe_context, indent=2)
        
        system_prompt = f"""
        You are an expert AI Business Advisor for a shopkeeper. 
        You have access to their Current Inventory Data Context.
        You also have access to a web search tool.
        
        INSTRUCTIONS:
        1. If the user asks about their own stock, reordering, or priorities, answer based on the Current Inventory Data.
        2. If the user asks about "current trends", "market trends", or general advice requiring live data, you MUST use the search tool to find up-to-date information on the internet.
        3. ALWAYS format your final response in Markdown (using bullet points, bold text, etc., as appropriate).
        
        Current Inventory Data Context:
        {context_str}
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])
        
        agent = create_tool_calling_agent(chat, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)
        
        response = agent_executor.invoke({"input": message})
        return response["output"]
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"⚠️ **Advisor Error**: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python universal_analyzer.py <path_to_csv_file>")
        print("Example: python universal_analyzer.py Sales.csv")
    else:
        target_csv = sys.argv[1]
        analyze_csv_file(target_csv)
