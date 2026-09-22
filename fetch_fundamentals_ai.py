import yfinance as yf
import pandas as pd
from openpyxl.utils import get_column_letter
from openai import OpenAI
import os
import json
from datetime import datetime

# ==========================================
# ⚙️ NVIDIA API 設定
# ==========================================
NVIDIA_API_KEY = "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"

client = OpenAI(
  base_url="https://integrate.api.nvidia.com/v1",
  api_key=NVIDIA_API_KEY
)

def ask_nvidia_llm_batch(stock_data_dict):
    """
    【進階批次處理版】餵入 8 大基本面指標，要求 LLM 給出 100 分制評分與分析
    """
    prompt = f"""
    你現在是一位華爾街資深量化分析師。
    我將提供一個包含多檔美股最新財報數據的 JSON。
    請為【每一檔】股票進行綜合評估，並給出以下兩項資訊：
    1. Score (整數 0-100)：根據所有提供的基本面數據打分。財務健康、成長性高、估值合理的分數越高。
    2. Analysis (約 100 字繁體中文)：詳細說明該公司的核心業務與產業，並解釋你給出這個分數的核心理由（點出數據中的亮點或隱憂）。

    📊 財報數據：
    {json.dumps(stock_data_dict, ensure_ascii=False, indent=2)}

    ⚠️ 【極度重要：輸出格式限制】
    你「必須」且「只能」輸出純 JSON 格式。不要有任何開場白、不要使用 Markdown 標籤 (```json)。
    請嚴格遵守以下 JSON 格式回覆：
    {{
        "股票代碼1": {{
            "Score": 85,
            "Analysis": "分析文字..."
        }},
        "股票代碼2": {{
            "Score": 60,
            "Analysis": "分析文字..."
        }}
    }}
    """
    
    try:
        completion = client.chat.completions.create(
            model="meta/llama-3.3-70b-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1, 
            max_tokens=2500 
        )
        
        # 獲取 AI 回覆
        ai_reply = completion.choices[0].message.content.strip()
        
        # 防呆機制：清除 AI 偶爾會自作主張加上的 Markdown 標籤
        if ai_reply.startswith("```json"):
            ai_reply = ai_reply[7:]
        if ai_reply.startswith("```"):
            ai_reply = ai_reply[3:]
        if ai_reply.endswith("```"):
            ai_reply = ai_reply[:-3]
            
        # 將字串轉換為 Python 的字典 (Dictionary)
        return json.loads(ai_reply.strip())
        
    except Exception as e:
        print(f"⚠️ NVIDIA API 批次呼叫或 JSON 解析失敗。錯誤細節: {e}")
        return {} # 發生錯誤時回傳空字典

def fetch_and_export_with_nvidia():
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n⚡ [{current_time_str}] 任務啟動：開始批次抓取基本面數據...")
    
    try:
        df_pool = pd.read_excel("Stock_Pool.xlsx")
        watch_list = df_pool['Ticker'].dropna().astype(str).tolist()
    except Exception as e:
        print("💡 提示：找不到 Stock_Pool.xlsx，採用預設測試名單。")
        watch_list = ["NVDA", "AAPL", "TSM"] 

    # 1️⃣ 第一階段：極速收集所有數據 (8大指標)
    all_stock_data = {}
    
    for ticker in watch_list:
        try:
            print(f"📥 正在下載 {ticker} 財報數據 ...")
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # 存入字典備用 (補齊 8 大指標)
            all_stock_data[ticker] = {
                "Revenue_Growth": info.get("revenueGrowth", 0) or 0,
                "ROE": info.get("returnOnEquity", 0) or 0,
                "PEG_Ratio": info.get("pegRatio", 2.0) or 2.0,
                "Operating_Margin": info.get("operatingMargins", 0) or 0,
                "Forward_PE": info.get("forwardPE", 0) or 0,
                "Price_To_Book": info.get("priceToBook", 0) or 0,
                "Debt_To_Equity": info.get("debtToEquity", 0) or 0,
                "Free_Cash_Flow": info.get("freeCashflow", 0) or 0
            }
        except Exception as e:
            print(f"⚠️ {ticker} 數據下載失敗: {e}")

    if not all_stock_data:
        print("❌ 沒有成功抓取到任何數據，任務中斷。")
        return

    # 2️⃣ 第二階段：一次性呼叫 LLM 進行批次分析
    print("\n☁️ 數據收集完畢！打包發送至 NVIDIA 雲端超級電腦進行【批次分析】...")
    ai_analyses_dict = ask_nvidia_llm_batch(all_stock_data)

    # 3️⃣ 第三階段：組合數據與 AI 報告，輸出 Excel 和 Markdown
    excel_results = []
    md_content = f"# 🤖 AI 美股基本面追蹤報告\n"
    md_content += f"> 報告生成時間：{current_time_str}\n\n"
    md_content += "---\n\n"

    # ✨ 新增：在 Excel 最後加入「不投資 (空手)」的欄位
    excel_results.append({
    "Portion": "", 
    "Ticker": "None",
    "AI_Score": "-",
    "Revenue_Growth": "-",
    "ROE": "-",
    "PEG_Ratio": "-",
    "Operating_Margin": "-",
    "Forward_PE": "-",
    "Price_To_Book": "-",
    "Debt_To_Equity": "-",
    "Free_Cash_Flow": "-"
    })

    for ticker, data in all_stock_data.items():
        # 安全取得 AI 回覆解析
        ai_data = ai_analyses_dict.get(ticker, {})
        if isinstance(ai_data, dict):
            ai_score = ai_data.get("Score", "N/A")
            ai_analysis = ai_data.get("Analysis", "⚠️ AI 未能生成此檔股票的分析。")
        else:
            ai_score = "N/A"
            ai_analysis = str(ai_data)

        # 整理 Excel 數據：新增 Portion 欄位在最前面
        excel_results.append({
            "Portion": "", # 留空讓使用者填寫資金比率
            "Ticker": ticker,
            "AI_Score": ai_score,
            "Revenue_Growth": data["Revenue_Growth"],
            "ROE": data["ROE"],
            "PEG_Ratio": data["PEG_Ratio"],
            "Operating_Margin": data["Operating_Margin"],
            "Forward_PE": data["Forward_PE"],
            "Price_To_Book": data["Price_To_Book"],
            "Debt_To_Equity": data["Debt_To_Equity"],
            "Free_Cash_Flow": data["Free_Cash_Flow"]
        })
        
        # 拼接 Markdown 報告
        md_content += f"## 📈 {ticker} (AI 評分: {ai_score})\n"
        md_content += f"- **營收成長率**：{data['Revenue_Growth']*100:.1f}%\n"
        md_content += f"- **股東權益報酬率 (ROE)**：{data['ROE']*100:.1f}%\n"
        md_content += f"- **本益成長比 (PEG)**：{data['PEG_Ratio']:.2f}\n"
        md_content += f"- **營業利益率**：{data['Operating_Margin']*100:.1f}%\n"
        md_content += f"- **預估本益比 (Forward P/E)**：{data['Forward_PE']:.2f}\n"
        md_content += f"- **股價淨值比 (P/B)**：{data['Price_To_Book']:.2f}\n"
        md_content += f"- **負債權益比 (D/E)**：{data['Debt_To_Equity']:.2f}\n\n"
        md_content += f"### 💡 AI 量化分析師建議：\n{ai_analysis}\n\n"
        md_content += "---\n\n"

    # ======= 輸出 1: 乾淨的 Excel 數據檔 =======
    df = pd.DataFrame(excel_results)
    excel_file = "AI_Stock_pool.xlsx"
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Fundamentals')
        worksheet = writer.sheets['Fundamentals']
        for i, col in enumerate(df.columns, 1): 
            col_letter = get_column_letter(i)
            max_len = max(df[col].astype(str).map(len).max(), len(str(col)))
            worksheet.column_dimensions[col_letter].width = max_len + 3

    # ======= 輸出 2: Markdown 報告檔 =======
    md_file = "AI_Analysis_Report.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"\n📊 [成功] 乾淨數據已寫入：{excel_file}")
    print(f"📝 [成功] AI 批次分析報告已寫入：{md_file}")
    print("✅ 單次任務執行完畢。請打開 AI_Stock_pool.xlsx 在 Portion 欄位填寫想投入的資金比率。")

if __name__ == "__main__":
    fetch_and_export_with_nvidia()