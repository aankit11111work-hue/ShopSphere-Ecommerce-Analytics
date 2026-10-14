import pandas as pd
import re
from rapidfuzz import process, fuzz
import numpy as np

pd.set_option("display.max_columns", None)

file_path = r"D:\Users\Ankit\Downloads\ShopSphere_Ecommerce_Raw_Data.xlsx"
customers = pd.read_excel(file_path, sheet_name="Customers")
products = pd.read_excel(file_path, sheet_name="Products")
orders = pd.read_excel(file_path, sheet_name="Orders")
returns = pd.read_excel(file_path, sheet_name="Returns")

"                                           Cleaning the Customer sheet                                                "

"Total no of rows and columns in customers excel sheet"
shape = customers.shape
# print(shape)

"To see what the first few rows looks like"
head = customers.head(2)
# print(head)

"Checking for NAN values and duplicates"
null_check = customers.isnull().sum()
print(null_check)
customers.info()
duplicates = customers.duplicated().sum()
print(duplicates)

"shows which row is duplicate and the original row"
display_duplicates_value = customers[customers.duplicated(keep=False)]

"show which row has the null value"
check_null_value = customers[customers["Age"].isnull()]
print(check_null_value)
print(display_duplicates_value)

"shows the full information of the row containing null value"
display_null_value = customers.loc[200]
print(display_null_value)
customers = customers.drop_duplicates(keep="first")

"checks the average and median values to replace the null value in the database"
print(customers["Age"].agg([
    "mean",
    "median"
]))
print(customers["Age"].describe())
customers["Age"] = customers["Age"].fillna(customers["Age"].median())
print(customers.loc[200])

"To check errors "
print(customers["City"].unique())
print(customers["Region"].unique())
print(customers["Customer_Segment"].unique())

"Fixing those errors and checking it"
customers["City"] = customers["City"].str.strip()
customers["Region"] = customers["Region"].str.strip().str.title()
print(customers["City"].unique())
print(customers["Region"].unique())

"Check for any typo, errors and special characters in customer name"
names = customers["Customer_Name"].dropna().str.strip().str.title().unique()
for name in names:
    if re.search(r"[^A-Za-z\s]", name):
        print("Unusual name", name)
for name in names:
    result = process.extract(
        name,
        names,
        scorer=fuzz.ratio,
        score_cutoff=90
    )
    for match in result:
        matched_name = match[0]
        score = match[1]
        if name != matched_name:
            print(name, "-", matched_name, score)

print("THE CUSTOMERS SHEET IS CLEANED")

"                                               Cleaning the products sheet                                            "

# print(products.columns.to_list())
# products.info()

"Check Duplicates and null"

duplicates_product = products.duplicated().sum()
null_check_products = products.isnull().sum()

print("Total Duplicates = ", duplicates_product)
print(" Total NaN = ", null_check_products)

" Correcting errors in category and sub category"

print(products["Category"].unique(),
      products["Sub_Category"].unique())

products["Category"] = products["Category"].str.strip().str.title()
products["Sub_Category"] = products["Sub_Category"].str.strip().str.title()
print(products["Category"].unique(),
      products["Sub_Category"].unique())

"Correcting any any errors in product names"

product_names = products["Product_Name"].str.strip().str.title().unique()

"Checking if product Id is unique "
print(products["Product_ID"].duplicated().sum())
print(products["Product_Name"].duplicated().sum())
print(products[
          (products["Cost_Price"] > products["Selling_Price"]) |
          (products["Selling_Price"] > products["Marked_Price"])
          ])

print("THE PRODUCT SHEET IS CLEANED")

"                                          Cleaning the orders sheet                                                   "

# orders.info()

"Checking for duplicates"
print("Total Duplicate = ", orders.duplicated().sum())
print(orders[orders.duplicated(keep=False)])

orders = orders.drop_duplicates(keep="first")

print("Total Duplicate = ", orders.duplicated().sum())
print("Total Duplicate Order ID =  ", orders["Order_ID"].duplicated().sum())

"checking for null"
print(orders.isnull().sum())
print(orders[orders["Discount"].isnull()])

print(products.index[products["Product_ID"] == "P085"].tolist())
print(products.loc[84])

print(orders[orders["Discount"].isnull()])

"bringing the selling price column in orders sheet"

orders["Selling_Price"] = orders["Product_ID"].map(
    products.set_index("Product_ID")["Selling_Price"]
)

"filling the null row"
orders["Discount"] = orders["Discount"].fillna(
    (orders["Selling_Price"] - orders["Unit_Price"])
    / orders["Selling_Price"]
)

"changing the discount into percentage for better understanding"

orders["Discount"] = orders["Discount"].mul(100)
print(orders.loc[35])

"creating a new column"

orders["Total_Value"] = orders["Unit_Price"].mul(orders["Quantity"])

"checking for relationship error"
# print("Unmatched customer in order sheet ID = ", "\n",orders[~orders["Customer_ID"].isin(customers["Customer_ID"])])
# print(customers[customers["Customer_ID"].str.contains("C0007", na=False)].to_string(index=False))

"repr shows hidden space"
# print(repr(orders.loc[120, "Customer_ID"]))
# print(repr(customers.loc[6, "Customer_ID"]))

"checking for product - order relationship error"
# print("Unmatched Product ID in order sheet = ", "\n", orders[~orders["Product_ID"].isin(products["Product_ID"])])
orders["Product_ID"] = orders["Product_ID"].str.upper()
print("Unmatched Product ID in order sheet = ", "\n", orders[~orders["Product_ID"].isin(products["Product_ID"])])

orders["Customer_ID"] = orders["Customer_ID"].str.strip()

"checking if quantity and discount value are logical"

# print(orders[orders["Quantity"] <= 0])
# print(orders[orders["Discount"] >= 100])


"checking if dates are correct"
# print(orders.nsmallest(5, "Order_Date")[["Order_ID", "Order_Date"]])
print(orders[orders["Order_ID"] == "O00751"])
print(customers[customers["Customer_ID"] == "C0088"])
print(products[products["Product_ID"] == "P098"])

"bringing product launch date into order page"
orders["Product_Launch_Date"] = orders["Product_ID"].map(
    products.set_index("Product_ID")["Product_Launch_Date"]
)

"Checking for illogical dates"
check_dates = orders[orders["Product_Launch_Date"] > orders["Order_Date"]]
# print(check_dates)

"ERROR IN DATA"
earliest_orders = (
    orders.groupby("Product_ID")["Order_Date"]
    .min()
    .reset_index(name="First_Order_Date")
)

product_check = products[["Product_ID", "Product_Launch_Date"]].merge(
    earliest_orders,
    on="Product_ID",
    how="left"
)
invalid_products = product_check[
    product_check["Product_Launch_Date"] >
    product_check["First_Order_Date"]
    ]

print(invalid_products[
          ["Product_ID", "Product_Launch_Date", "First_Order_Date"]])
print(
    orders["Order_Date"]
    .dt.year
    .value_counts()
    .sort_index()
)
orders["Date_Status"] = "Valid"
orders.loc[orders["Order_Date"].dt.year == 2023,
"Date_Status"] = "Outside Date Range"

"checking is the order date is before customer join date "
earliest_orders_per_customer = (
    orders.groupby("Customer_ID")["Order_Date"]
    .min()
    .reset_index()
)
date_check = customers[["Customer_ID", "Customer_Join_Date"]].merge(
    earliest_orders_per_customer,
    on="Customer_ID",
    how="left"
)
invalid_date = date_check[date_check["Customer_Join_Date"] > date_check["Order_Date"]]
print(invalid_date)

print("THE ORDERS SHEET IS CLEANED")

"                                       Checking and cleaning the return sheet                                         "

"Checking for null and duplicates"

print(returns.isnull().sum())
print("Total Duplicates = ", returns.duplicated().sum())
print(
    returns["Return_ID"].duplicated().sum(),
    "\n",
    returns["Order_ID"].duplicated().sum(),
    sep=""
)
print(returns[returns["Return_Cost"].isnull()])

"Correcting errors in product condition and return reasons"
print(returns["Product_Condition"].unique())
print(returns["Return_Reason"].unique())

returns["Product_Condition"] = returns["Product_Condition"].str.strip().str.title()
returns["Return_Reason"] = returns["Return_Reason"].str.strip().str.title()

print(returns["Product_Condition"].unique())
print(returns["Return_Reason"].unique())

"Filling the NaN in Return cost column "

"bring unit price column"
returns["Unit_Price"] = returns["Order_ID"].map(
    orders.set_index("Order_ID")["Unit_Price"]
)

search = returns["Return_Cost"].isna()

"calculating the return percentage"
returns["Actual_Pct"] = (
        returns["Return_Cost"] /
        (returns["Unit_Price"] * returns["Quantity_Returned"])
)

"finding out the pattern on how the returns are calculated"

print(returns.groupby(
    ["Product_Condition", "Return_Reason"]
)["Actual_Pct"].describe())
pct = returns.loc[
    (returns["Product_Condition"] == "Good") &
    (returns["Return_Reason"] == "Wrong Product") &
    returns["Return_Cost"].notna(),
    "Actual_Pct"
].median()

returns.loc[search, "Return_Cost"] = (
        returns.loc[search, "Unit_Price"]
        * returns.loc[search, "Quantity_Returned"]
        * pct
)
returns["Actual_Pct"] = (
        returns["Return_Cost"] /
        (returns["Unit_Price"] * returns["Quantity_Returned"])
)
returns["Return_Cost"] = returns["Return_Cost"].astype(int)
print(returns.loc[100])
print(returns.head(5).to_string(index=False))

"checking for relationship error in return sheet"
# print(returns[returns["Return_Cost"] <= 0])
# print("Unmatched order ID in return sheet = ", "\n",returns[~returns["Order_ID"].isin(orders["Order_ID"])])

"checking if quantity returned is more than quantity bought"
total_returns = (
    returns.groupby("Order_ID")["Quantity_Returned"]
    .sum()
    .reset_index()
)
check = total_returns.merge(
    orders[["Order_ID", "Quantity"]],
    on="Order_ID",
    how="left"
)
check = check[
    check["Quantity_Returned"] > check["Quantity"]]

print("Irregular Quantity Returned =\n", check)

print("THE RETURN SHEET IS CLEANED")


"creating new cleaned tables"
customers_cleaned = customers.copy()
products_cleaned = products.copy()
orders_cleaned = orders.copy()
returns_cleaned = returns.copy()

returns_cleaned = returns_cleaned.drop(columns=["Actual_Pct"])

with pd.ExcelWriter("ShopSphere_Ecommerce_Cleaned_Data.xlsx") as writer:
    customers_cleaned.to_excel(writer, sheet_name="Customers", index=False)
    products_cleaned.to_excel(writer, sheet_name="Products", index=False)
    orders_cleaned.to_excel(writer, sheet_name="Orders", index=False)
    returns_cleaned.to_excel(writer, sheet_name="Returns", index=False)