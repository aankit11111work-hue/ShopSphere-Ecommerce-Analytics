--Create Database Shopsphere
Use Shopsphere

Select DB_NAME()
CREATE TABLE Customers(
Customer_ID VARCHAR(10) PRIMARY KEY,
Customer_Name VARCHAR(100),
Gender VARCHAR(10),
Age INT,
City VARCHAR(100),
State VARCHAR(50),
Region VARCHAR(20),
Customer_Segment VARCHAR(10),
Customer_Join_Date DATE
);
SELECT *
FROM Customers


CREATE TABLE Products(
Product_ID VARCHAR(10) PRIMARY KEY,
Product_Name VARCHAR(100),
Category VARCHAR(100),
Sub_Category VARCHAR(100),
Marked_Price DECIMAL(10,2), 
Cost_Price DECIMAL(10,2),
Selling_Price DECIMAL(10,2),
Product_Launch_Date DATE
);


CREATE TABLE Orders(
Order_ID VARCHAR(10) PRIMARY KEY,
Order_Date DATE,
Customer_ID VARCHAR(10) FOREIGN KEY REFERENCES Customers(Customer_ID),
Product_ID VARCHAR(10) FOREIGN KEY REFERENCES Products(Product_ID),
Quantity INT,
Discount DECIMAL(4,2),
Unit_Price DECIMAL(10,2),
Selling_Price DECIMAL(10,2),
Total_Value DECIMAL(10,2),
Product_Launch_Date DATE,
Date_Status VARCHAR(20)
);


CREATE TABLE Returns(
Return_ID VARCHAR(10) PRIMARY KEY,
Order_ID VARCHAR(10) FOREIGN KEY REFERENCES Orders(Order_ID),
Return_Date DATE,
Return_Reason VARCHAR(20),
Quantity_Returned INT,
Return_Cost	DECIMAL(10,2),
Product_Condition VARCHAR(20),
Unit_Price DECIMAL(10,2)	
);

SELECT TOP 5 * FROM Customers;
SELECT TOP 5 * FROM Products;
SELECT TOP 5 * FROM Orders;
SELECT TOP 5 * FROM Returns;


--Customer demograpy  
SELECT Age, COUNT(Customer_ID) AS Customer_Per_Age   
FROM Customers
GROUP BY Age
ORDER BY AGE;

SELECT State, COUNT(Customer_ID) AS Customer_Per_State
FROM Customers
GROUP BY State;


SELECT 
  Order_ID, 
  COUNT (*) 
FROM Returns
GROUP BY Order_ID
HAVING COUNT(*)>1
ORDER BY Order_ID;


--Calculation of financials 
GO

CREATE OR ALTER VIEW Product_Summary AS
SELECT 
 o.Product_ID,
 SUM(o.Quantity) AS Quantity_Ordered, 

 SUM(COALESCE(r.Return_Cost,0)) AS Total_Return_Cost,

 SUM(COALESCE(r.Quantity_Returned ,0)) AS Quantity_Returned, 

 SUM(o.Quantity)-SUM(COALESCE(r.Quantity_Returned,0)) AS Quantity_Sold,
 
 p.Cost_Price * (
 SUM(o.Quantity)
 -SUM(COALESCE(r.Quantity_Returned,0))
 ) AS Total_Cost_Price,
 
 SUM(o.Total_Value) AS Total_Sales_Value,

 SUM(o.Unit_Price * 
 (o.Quantity-
 COALESCE(r.Quantity_Returned,0))
 )AS Net_Sales,

CAST(
 SUM(COALESCE(r.Quantity_Returned, 0)) *100.0
 / NULLIF(SUM(o.Quantity),0)
 AS DECIMAL(6,2)) AS  Return_Pct

FROM Orders o

LEFT JOIN 
Returns r
  ON o.Order_ID = r.Order_ID

LEFT JOIN Products p
  ON o.Product_ID = p.Product_ID
  WHERE o.Order_Date >= '2024-01-01'

GROUP BY 
  o.Product_ID,
  p.Cost_Price;
GO

GO
CREATE OR ALTER VIEW Product_Order_Detail AS
SELECT
    o.Order_ID,
    o.Product_ID,
    c.Customer_ID,
    o.Order_Date,
    o.Quantity,
    o.Unit_Price,
    o.Total_Value,

    COALESCE(r.Quantity_Returned, 0) AS Quantity_Returned,
    COALESCE(r.Total_Return_Cost, 0) AS Total_Return_Cost,

    o.Quantity - COALESCE(r.Quantity_Returned, 0) AS Quantity_Sold,

    o.Unit_Price *
        (o.Quantity - COALESCE(r.Quantity_Returned, 0)) AS Net_Sales

FROM Orders o

LEFT JOIN
(
    SELECT
        Order_ID,
        SUM(COALESCE(Quantity_Returned, 0)) AS Quantity_Returned,
        SUM(COALESCE(Return_Cost, 0)) AS Total_Return_Cost
    FROM Returns
    GROUP BY Order_ID
) r
    ON o.Order_ID = r.Order_ID

LEFT JOIN Customers c
    ON o.Customer_ID = c.Customer_ID

WHERE o.Order_Date >= '2024-01-01';
GO


WITH Financial_Summary AS(
SELECT
  (SUM(Total_Cost_Price) 
  + SUM(Total_Return_Cost)) AS Total_Expenditure,
  SUM(Net_Sales) AS Net_Sales,
  
  SUM(Net_Sales) 
  - (SUM(Total_Cost_Price) + 
  SUM(Total_Return_Cost)) AS Profit
FROM Product_Summary
)

SELECT	 
 Total_Expenditure, 
 Net_Sales, 
 Profit,

CAST(	
 (Profit
 /NULLIF(Total_Expenditure ,0)) * 100.0
 AS DECIMAL(6,2)
) AS Profit_Pct,

CAST(	
 (Profit
 /NULLIF(Net_Sales ,0)) * 100.0
 AS DECIMAL(6,2)
) AS Profit_Margin

FROM Financial_Summary;


--Calculating Discount change

WITH Monthly_Discount AS(
SELECT
  YEAR(Order_Date) AS Year,
  MONTH(Order_Date) AS Month,
  AVG(Discount) AS AVG_Discount
FROM Orders
WHERE Order_Date >= '01/01/2024'
GROUP BY
  YEAR(Order_Date),
  MONTH(Order_Date)
),
Discount_Change AS(
SELECT 
 Year,
 Month,
 AVG_Discount,
 LAG(AVG_Discount) OVER (
 ORDER BY Year, Month
 ) AS Previous_Month
FROM Monthly_Discount
)	

SELECT  
 Year,
 Month,
 AVG_Discount,
 Previous_Month,
 
 CAST(
  (AVG_Discount -
  Previous_Month) *100.0/
  NULLIF(Previous_Month, 0) AS DECIMAL(6,2)) AS MOM

FROM
Discount_Change
ORDER BY
 Year,
 Month;