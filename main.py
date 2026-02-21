import pandas as pd
import numpy as np

# ==============================
# 1️⃣ LOAD CSV FILES
# ==============================

importer = pd.read_csv("importer.csv")
exporter = pd.read_csv("exporter.csv")
news = pd.read_csv("globalnews.csv")

print("Files Loaded Successfully ✅")

# ==============================
# 2️⃣ BASIC CLEANING
# ==============================

# Remove duplicates
importer.drop_duplicates(inplace=True)
exporter.drop_duplicates(inplace=True)
news.drop_duplicates(inplace=True)

# Replace NA / empty strings
importer.replace(["NA", ""], np.nan, inplace=True)
exporter.replace(["NA", ""], np.nan, inplace=True)
news.replace(["NA", ""], np.nan, inplace=True)

# Drop rows where ID missing
importer.dropna(subset=["Buyer_ID"], inplace=True)
exporter.dropna(subset=["Exporter_ID"], inplace=True)

# ==============================
# 3️⃣ HANDLE MISSING VALUES
# ==============================

def clean_dataframe(df):
    numeric_cols = df.select_dtypes(include=np.number).columns
    categorical_cols = df.select_dtypes(include="object").columns

    # Fill numeric with median
    for col in numeric_cols:
        df[col] = df[col].fillna(df[col].median())

    # Fill categorical with "Unknown"
    for col in categorical_cols:
        df[col] = df[col].fillna("Unknown")

    return df

importer = clean_dataframe(importer)
exporter = clean_dataframe(exporter)
news = clean_dataframe(news)

# ==============================
# 4️⃣ REMOVE OUTLIERS (IQR METHOD)
# ==============================

def remove_outliers_iqr(df, column):
    if column not in df.columns:
        return df

    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1

    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR

    return df[(df[column] >= lower) & (df[column] <= upper)]

important_importer_cols = [
    "Revenue_Size_USD",
    "SalesNav_ProfileVisits",
    "Intent_Score",
    "Response_Probability"
]

important_exporter_cols = [
    "Revenue_Size_USD",
    "Manufacturing_Capacity_Tons",
    "Shipment_Value_USD",
    "Intent_Score"
]

for col in important_importer_cols:
    importer = remove_outliers_iqr(importer, col)

for col in important_exporter_cols:
    exporter = remove_outliers_iqr(exporter, col)

print("Outliers Removed ✅")

# ==============================
# 5️⃣ KEEP IMPORTANT FEATURES ONLY
# ==============================

importer_keep = [
    "Buyer_ID", "Country", "Industry",
    "Revenue_Size_USD", "Team_Size", "Certification",
    "Good_Payment_History", "Intent_Score",
    "Preferred_Channel", "Response_Probability",
    "Tariff_News", "StockMarket_Shock",
    "War_Event", "Natural_Calamity", "Currency_Fluctuation"
]

exporter_keep = [
    "Exporter_ID", "State", "Industry",
    "Revenue_Size_USD", "Manufacturing_Capacity_Tons",
    "Team_Size", "Certification",
    "Intent_Score", "Shipment_Value_USD",
    "Tariff_Impact", "StockMarket_Impact",
    "War_Risk", "Natural_Calamity_Risk", "Currency_Shift"
]

importer = importer[importer_keep]
exporter = exporter[exporter_keep]

# ==============================
# 6️⃣ BUILD RAG TEXT
# ==============================

def build_importer_text(row):
    return f"""
Buyer from {row['Country']} in {row['Industry']} industry.
Revenue {row['Revenue_Size_USD']} USD.
Team size {row['Team_Size']}.
Certification {row['Certification']}.
Intent score {row['Intent_Score']}.
Payment history {row['Good_Payment_History']}.
Preferred channel {row['Preferred_Channel']}.
Response probability {row['Response_Probability']}.
Risk factors: Tariff {row['Tariff_News']}, 
Stock market {row['StockMarket_Shock']}, 
War {row['War_Event']}, 
Natural calamity {row['Natural_Calamity']}, 
Currency fluctuation {row['Currency_Fluctuation']}.
"""

def build_exporter_text(row):
    return f"""
Exporter from {row['State']} in {row['Industry']} industry.
Revenue {row['Revenue_Size_USD']} USD.
Manufacturing capacity {row['Manufacturing_Capacity_Tons']} tons.
Team size {row['Team_Size']}.
Certification {row['Certification']}.
Intent score {row['Intent_Score']}.
Shipment value {row['Shipment_Value_USD']}.
Risk exposure: Tariff {row['Tariff_Impact']}, 
Stock market {row['StockMarket_Impact']}, 
War {row['War_Risk']}, 
Natural calamity {row['Natural_Calamity_Risk']}, 
Currency shift {row['Currency_Shift']}.
"""

importer["rag_text"] = importer.apply(build_importer_text, axis=1)
exporter["rag_text"] = exporter.apply(build_exporter_text, axis=1)

print("RAG Text Generated ✅")

# ==============================
# 7️⃣ SAVE CLEANED FILES
# ==============================

importer.to_csv("cleaned_importer.csv", index=False)
exporter.to_csv("cleaned_exporter.csv", index=False)

print("All Cleaning Completed Successfully 🚀")
print("Final Importer Shape:", importer.shape)
print("Final Exporter Shape:", exporter.shape)