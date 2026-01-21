#将.xlsx 文件转换为 .csv 文件
import pandas as pd

xlsx_path = r"F:\VSproject\CapacityModel\ExcelData\五轴加工中心一组.xlsx"
csv_path  = r"F:\VSproject\CapacityModel\五轴加工中心一组.csv"

df = pd.read_excel(xlsx_path, sheet_name=0)  # 第一个 sheet
df.to_csv(csv_path, index=False, encoding="utf-8-sig")
