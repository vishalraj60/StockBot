# 🏪 Autonomous Demand-Based Inventory System

An intelligent inventory management system that automatically analyzes demand trends, monitors stock levels, and triggers reorders for products based on sales velocity and market trends.

## 🚀 How It Works

### 1. **Demand Analysis**
- **Trend Detection**: Analyzes sales history to identify increasing, decreasing, stable, or explosive demand patterns
- **Sales Velocity**: Calculates average daily sales and demand acceleration
- **Pattern Recognition**: Identifies trending products and seasonal variations

### 2. **Stock Monitoring**
- **Real-time Tracking**: Continuously monitors current inventory levels
- **Reorder Point Calculation**: Automatically calculates optimal reorder points using:
  ```
  Reorder Point = (Average Daily Sales × Lead Time) + Safety Stock
  ```
- **Safety Stock**: Maintains buffer stock based on demand variability

### 3. **Automatic Reordering**
- **Intelligent Triggers**: Automatically initiates reorders when stock falls below reorder point
- **Quantity Optimization**: Calculates optimal order quantities considering:
  - Projected demand for next 14-21 days
  - Storage capacity constraints
  - Current stock levels
- **Priority Handling**: Prioritizes high-demand and trending products

### 4. **Emergency Response**
- **Stockout Detection**: Immediate alerts when products run out of stock
- **Express Shipping**: Cost-benefit analysis for expedited shipping
- **Lost Revenue Prevention**: Calculates potential revenue loss and justifies emergency actions

## 📊 System Components

### Core Files

- **`agent.py`** - AI agent with inventory management expertise
- **`task.py`** - Three analysis scenarios (single product, multi-product, emergency)
- **`main.py`** - System demonstration with all scenarios
- **`inventory_data.py`** - Data structures and business logic

### Key Features

#### 🔍 **Trend Analysis**
- Explosive growth detection (>50% increase)
- Steady growth identification (10-50% increase)
- Decline warning (<-10% change)
- Stable demand recognition

#### 📈 **Reorder Logic**
```
1. Calculate daily average sales
2. Determine demand trend
3. Compute reorder point
4. Assess urgency level
5. Calculate optimal quantity
6. Generate reorder recommendation
```

#### 🚨 **Urgency Levels**
- **CRITICAL**: Out of stock (0 units)
- **HIGH**: Below reorder point
- **MEDIUM**: Approaching reorder point
- **LOW**: Normal stock levels

## 🏬 Example Scenarios

### Scenario 1: Trending Product
```
Product: Chips
Current Stock: 10 units
Sales Trend: [15, 20, 25, 30, 35, 40, 45] (increasing)
Analysis: High demand growth detected
Action: Reorder 85 units immediately
```

### Scenario 2: Multi-Product Shop
```
Shop Inventory:
- Chips: 5 units (trending up) → HIGH PRIORITY
- Soda: 50 units (stable) → NORMAL
- Cookies: 0 units (out of stock) → CRITICAL
- Water: 100 units (declining) → LOW PRIORITY

Action: Reorder Cookies (critical), then Chips (high priority)
```

### Scenario 3: Emergency Stockout
```
Product: Chocolate Bars
Status: OUT OF STOCK (2 days)
Lost Sales: $200/day
Trend: Explosive growth
Decision: Use express shipping (+20% cost) to minimize losses
```

## 🛠️ Installation & Setup

### Prerequisites
```bash
pip install crewai langchain-groq
```

### Configuration
1. Set your Groq API key in `agent.py`
2. Configure product data and sales history
3. Adjust safety stock percentages and lead times

### Running the System

#### Full Demonstration
```bash
python main.py
```

#### Individual Scenarios
```python
# Single product analysis
python main.py --scenario single

# Multi-product analysis  
python main.py --scenario multi

# Emergency response
python main.py --scenario emergency
```

## 📋 Business Logic

### Reorder Point Formula
```
Reorder Point = (Average Daily Sales × Lead Time) + Safety Stock
Safety Stock = Average Daily Sales × Safety Stock Percentage
```

### Optimal Order Quantity
```
If out of stock: Cover next 14 days
If normal reorder: Cover next 21 days
Quantity = Projected Demand - Current Stock
Quantity = min(Quantity, Storage Capacity - Current Stock)
```

### Priority Ranking
1. **Critical** (Out of stock)
2. **High** (Below reorder point + increasing trend)
3. **Medium** (Below reorder point)
4. **Low** (Normal stock)

## 🎯 Key Benefits

### ✅ **Prevents Stockouts**
- Proactive monitoring and automatic reordering
- Emergency response for critical situations

### ✅ **Optimizes Inventory**
- Reduces overstocking and holding costs
- Maintains optimal safety stock levels

### ✅ **Maximizes Revenue**
- Identifies and prioritizes trending products
- Prevents lost sales opportunities

### ✅ **Cost-Effective**
- Intelligent quantity calculations
- Cost-benefit analysis for express shipping

### ✅ **Scalable**
- Handles single products to entire inventory
- Adaptable to different business sizes

## 🔧 Customization

### Adding New Products
```python
# In inventory_data.py
Product("P006", "New Product", "Category", price, lead_time, capacity, safety_pct)
```

### Adjusting Parameters
- **Safety Stock**: Modify `safety_stock_percentage`
- **Lead Times**: Update `supplier_lead_time`
- **Storage Limits**: Set `storage_capacity`

### Integration Points
- POS systems for real-time sales data
- Supplier APIs for automatic ordering
- ERP systems for inventory tracking

## 📈 Performance Metrics

### Key Indicators
- **Stockout Rate**: Percentage of time products are out of stock
- **Inventory Turnover**: How quickly inventory is sold and replaced
- **Carrying Costs**: Cost of holding inventory
- **Lost Revenue**: Sales lost due to stockouts

### Optimization Goals
- Minimize stockouts (<1%)
- Maximize inventory turnover
- Reduce carrying costs by 20-30%
- Eliminate lost revenue from stockouts

## 🚀 Future Enhancements

### Planned Features
- **Machine Learning**: Advanced demand forecasting
- **Seasonal Adjustments**: Automatic seasonal trend detection
- **Supplier Integration**: Direct API ordering
- **Dashboard**: Real-time inventory visualization
- **Mobile Alerts**: SMS/email notifications

### Advanced Analytics
- **ABC Analysis**: Classify products by revenue contribution
- **EOQ Optimization**: Economic Order Quantity calculations
- **Demand Elasticity**: Price sensitivity analysis
- **Competitor Monitoring**: Market trend integration

---

## 📞 Support

For questions or customization requests:
1. Review the code comments in each file
2. Check the example scenarios in `task.py`
3. Examine the data structures in `inventory_data.py`

**System Status**: ✅ Fully functional with AI-powered decision making
