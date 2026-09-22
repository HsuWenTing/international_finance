import schedule
import time
# 這裡將我們寫好的腳本引入 (注意：檔名不要打 .py)
from fetch_fundamentals_ai import fetch_and_export_with_nvidia

# ==========================================
# ⏱️ 5 分鐘自動化排程監聽核心
# ==========================================

def job():
    print("\n" + "="*50)
    print("⏰ 排程時間到！啟動 AI 基本面掃描任務...")
    # 呼叫另一支檔案裡面的主函數
    fetch_and_export_with_nvidia()
    print("💤 任務結束，進入休眠，等待下一個 5 分鐘週期...")
    print("="*50)

if __name__ == "__main__":
    # 程式啟動時，先毫不猶豫地執行第一次
    print("🚀 啟動排程管理員：立刻執行首次任務...")
    fetch_and_export_with_nvidia()
    
    # 設定排程器：每 5 分鐘執行一次 job 函數
    schedule.every(5).minutes.do(job)
    
    print("\n==================================================")
    print("🕒 5分鐘自動化測試流水線已成功部署！")
    print("程式正在即時監聽系統時間，請勿關閉此終端機視窗...")
    print("==================================================")
    
    # 無限迴圈監聽系統時間
    while True:
        schedule.run_pending()
        time.sleep(1) # 每秒檢查一次排程狀態