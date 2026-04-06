import os
import sys
import csv
from crewai import Task, Crew
from universal_csv_agent import predictive_agent

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
                # Hard limit set to 30 to guarantee we stay completely under the 12000 token TPM limit
                if len(data_sample) < 30:  
                    # Extract only efficient columns and strictly truncate values to 40 chars max
                    trimmed_row = {k: (str(row[k])[:40] + '...' if row[k] and len(str(row[k])) > 40 else row[k]) for k in keep_columns}
                    data_sample.append(trimmed_row)
    except Exception as e:
        error_msg = f"❌ Failed to load CSV '{csv_path}': {str(e)}"
        print(error_msg)
        return error_msg
    
    task_description = f"""
    The user has provided a CSV file representing shop data. 
    Total Products (Rows): {total_rows}
    Available Columns/Features: {columns}
    
    Here is a small sample of the data (up to 10 rows):
    {data_sample}

    YOUR GOAL:
    1. Carefully look at the columns. Identify which columns might indicate 'Stock/Inventory/Availability' and which might indicate 'Sales/Trend/Popularity/Demand'.
    2. If explicit 'stock' columns are missing, DO NOT panic. Use logical proxies instead (e.g., highly discounted items, highly rated items, or items with missing data fields could be inferred as trending/high demand).
    3. Analyze the provided sample data under these assumptions to determine which items are TRULY low in stock, and which are TRULY high trend.
    4. You MUST be highly selective and accurate. DO NOT just list every single product in both categories! Evaluate each product and ONLY place it in a category if it legitimately qualifies. A product can be in one list, both lists, or NEITHER list.
       You MUST separate your findings into EXACTLY two lists under these exact h3 headings:
       
       ### 📉 Low Stock Items
       [List ONLY the items that are genuinely low in stock/availability here. For EACH product in this list, you MUST display BOTH its Product Name and its actual Stock/Quantity value from the data (e.g., 'Product Name - 10 units'). Limit to Name and Stock level only.]
       
       ### 🚀 High Trend Sellers
       [List ONLY the highly popular/trending items here. For EACH product in this list, you MUST display BOTH its Product Name and the specific metric indicating its trend from the data (e.g., 'Product Name - 50% discount' or 'Product Name - High Sales'). Limit to Name and Trend metric only.]
       
    5. AFTER the two lists, in a SEPARATE SECTION titled '### 📊 Comprehensive Explanation', for EACH item located in both lists, provide a DEEP, COMPREHENSIVE EXPLANATION detailing the specific metrics (e.g., high discount rates, stellar user ratings, price drops) that signify its status, and explicitly explain the business urgency.

    Format your output cleanly in Markdown. Focus entirely on exhaustively assigning the items to these two categories and displaying the required Name + Stock/Trend metric in the lists themselves.
    """

    prediction_task = Task(
        description=task_description,
        agent=predictive_agent,
        expected_output="A structured markdown report identifying the top 5 low-stock/high-trend items, along with an explanation of CSV semantics."
    )

    crew = Crew(
        agents=[predictive_agent],
        tasks=[prediction_task],
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
        return output_data
    except Exception as e:
        error_str = str(e)
        print(f"❌ AI Analysis Error: {error_str}")
        return f"**AI Analysis Error**: {error_str}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python universal_analyzer.py <path_to_csv_file>")
        print("Example: python universal_analyzer.py Sales.csv")
    else:
        target_csv = sys.argv[1]
        analyze_csv_file(target_csv)
