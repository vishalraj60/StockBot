import os
import sys
import csv
from crewai import Task, Crew
from universal_csv_agent import predictive_agent, strategist_agent

def calculate_inventory_metrics(data_sample):
    if not data_sample: return data_sample
    
    # Try to find columns
    keys = data_sample[0].keys()
    stock_col = next((k for k in keys if any(w in k.lower() for w in ['stock', 'qty', 'quantity', 'inventory'])), None)
    sales_col = next((k for k in keys if any(w in k.lower() for w in ['sales', 'sold', 'demand', 'velocity'])), None)
    
    for row in data_sample:
        try:
            # Parse or simulate data
            stock_val = str(row[stock_col]).replace(',', '') if stock_col and row.get(stock_col) else '0'
            stock = float(''.join(filter(str.isdigit, stock_val)) or 0)
            
            sales_val = str(row[sales_col]).replace(',', '') if sales_col and row.get(sales_col) else '5'
            sales = float(''.join(filter(str.isdigit, sales_val)) or 5.0)
            
            lead_time = 7 # default 7 days lead time
            
            safety_stock = sales * 0.20 # 20% safety stock
            reorder_point = (sales * lead_time) + safety_stock
            
            priority = "LOW"
            if stock <= 0:
                priority = "CRITICAL"
            elif stock < reorder_point:
                priority = "HIGH"
            elif stock < reorder_point * 1.5:
                priority = "MEDIUM"
                
            row['System_Priority'] = priority
            row['Reorder_Point_Formula'] = f"({sales} daily x {lead_time} days) + {round(safety_stock,1)} = {round(reorder_point, 1)}"
        except Exception:
            row['System_Priority'] = "UNKNOWN"
            
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
    
    Here is a small sample of the data (up to 10 rows). Note that we have pre-calculated 'System_Priority' and 'Reorder_Point_Formula' for you using our internal mathematical models:
    {data_sample}

    YOUR GOAL:
    1. Read the provided CSV data which now includes our internal Reorder_Point and System_Priority calculations.
    2. Incorporate the System_Priority (CRITICAL, HIGH, MEDIUM, LOW) into your analysis. 
    3. Evaluate each product and group them EXACTLY into these exact h3 headings:
       
       ### 🚨 Critical / High Priority (Action Required)
       [List ONLY items that have a CRITICAL or HIGH System_Priority, or genuinely look like they are out of stock. For EACH product, display the Name, its calculated Priority, and explain briefly WHY based on the formula and trends.]
       
       ### 🚀 High Trend Sellers
       [List highly popular/trending items here based on sales velocity or implicit demand proxies.]
       
    4. AFTER the two lists, in a SEPARATE SECTION titled '### 📊 Comprehensive Explanation', explain the formula logic used (Reorder Point = (Daily Sales x Lead Time) + Safety Stock) and how it influenced your categorization.

    Format your output cleanly in Markdown. Focus entirely on exhaustively assigning the items to these categories.
    """

    prediction_task = Task(
        description=task_description,
        agent=predictive_agent,
        expected_output="A structured markdown report identifying the top low-stock/high-trend items, along with an explanation of CSV semantics."
    )

    strategy_task = Task(
        description="""
        Review the outcome of the Data Analyst. Identify the 🚨 Critical / High Priority items.
        For each of these emergency items, append a section titled '### 🚚 Emergency Shipping & Logistics Plan'.
        In this section, provide a brief cost-benefit analysis of using Standard Shipping (cheaper but slower) vs Express Shipping (costlier but prevents lost sales) based on the item's priority level.
        Do not repeat the Analyst's lists. Just add your new Logistics section to the bottom of the final report.
        """,
        agent=strategist_agent,
        expected_output="The final markdown report containing the analyst's findings PLUS the new Emergency Shipping & Logistics Plan section."
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

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python universal_analyzer.py <path_to_csv_file>")
        print("Example: python universal_analyzer.py Sales.csv")
    else:
        target_csv = sys.argv[1]
        analyze_csv_file(target_csv)
