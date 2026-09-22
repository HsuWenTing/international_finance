import pandas as pd
import os

def calculate_and_export_csv():
    excel_file = "AI_Stock_pool.xlsx"
    csv_file = "trade_list.csv"

    if not os.path.exists(excel_file):
        print(f"找不到 {excel_file}，請先執行抓取基本面腳本。")
        return

    # 1. 讀取 Excel
    df = pd.read_excel(excel_file)

    # 防呆檢查：確認有沒有 Portion 欄位
    if 'Portion' not in df.columns:
        print("找不到 'Portion' 欄位，請確定使用的是最新產出的 Excel。")
        return

    # 2. 將 Portion 轉為數值，並填補空格為 0
    df['Portion'] = pd.to_numeric(df['Portion'], errors='coerce').fillna(0)

    # 篩選出 Portion 大於 0 的股票
    selected_df = df[df['Portion'] > 0].copy()

    if selected_df.empty:
        print("你在 Excel 中沒有為任何股票設定大於 0 的 Portion，無法產出 CSV。")
        return

    print(f"你設定了 {len(selected_df)} 檔股票的 Portion，正在計算資金權重...")

    # 3. 依照 Portion 比例計算投入資金的百分比 (% )
    total_portion = selected_df['Portion'].sum()
    selected_df['Alloc_Percent'] = (selected_df['Portion'] / total_portion) * 100

    # 4. 格式化並匯出給 MT5 的 CSV (只需要代碼和百分比)
    # ⚠️ 重要防呆：過濾掉 "不投資"，因為 MT5 沒有這個交易商品會導致 EA 報錯
    output_df = selected_df[selected_df['Ticker'] != 'None'][['Ticker', 'Alloc_Percent']].copy()
    output_df['Alloc_Percent'] = output_df['Alloc_Percent'].round(2) # 取到小數點後兩位

    mt5_path = r"/Users/hsuwenting/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/Program Files/MetaTrader 5/MQL5/Files"
    
    # 防呆機制：如果 MT5 的路徑不存在，就輸出在當前資料夾
    if os.path.exists(mt5_path):
        csv_file_path = os.path.join(mt5_path, "trade_list.csv")
    else:
        print(f"⚠️ 找不到 MT5 指定路徑，將改匯出於目前目錄...")
        csv_file_path = csv_file

    output_df.to_csv(csv_file_path, index=False, header=False) # MT5 不需要標題列
    
    print(f"\n成功匯出 MT5 專用名單：{csv_file_path}")
    print(output_df)

if __name__ == "__main__":
    calculate_and_export_csv()