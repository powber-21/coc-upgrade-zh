# 部落衝突升級數據

### 👉 [打開網頁：powber-21.github.io/coc-upgrade-zh](https://powber-21.github.io/coc-upgrade-zh)

部落衝突（Clash of Clans）所有建築、兵種、法術、英雄、裝備與戰寵的升級費用、時間和屬性，繁體中文介面。

- 家鄉村莊、建築大師基地、部落首都完整數據
- 依大本營等級查詢每個項目的等級上限與數量
- 月卡折扣換算
- 每天自動檢查資料更新

**加到 iPhone 主畫面：** 用 Safari 打開網頁 → 分享 →「加入主畫面」。

## 運作方式

- `build.py` 把 [clash-of-clans-data](https://github.com/chiefpansancolt/clash-of-clans-data) 的 JSON 轉成單一網頁
- `zh.json` 是所有中文翻譯（名稱、欄位、攻擊模式、數值文字）
- GitHub Actions（`.github/workflows/deploy.yml`）每天台灣時間 04:00 檢查資料，有更新就重新產生並發佈到 GitHub Pages

## 授權

數據與圖片來源見 [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md)。

This material is unofficial and is not endorsed by Supercell. For more information see Supercell's Fan Content Policy: www.supercell.com/fan-content-policy.
