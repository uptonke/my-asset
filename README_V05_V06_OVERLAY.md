# v0.5 Component VaR / ES + v0.6 Risk Budgeting / HRP-lite

Base:
- v031_frontend_cleanup_v04_ewma_overlay.zip

覆蓋檔案：
- index.html
- scripts/update_stock_meta.py
- update_stock_meta.py
- data/quant_ticker_map.json
- assets/js/app.bundle.js
- assets/js/terminal-ia-phase2.js

v0.5 新增：
- historical Component VaR 95 / 99
- historical Component ES 95 / 99
- Top component ES contributors
- Top 3 ES concentration
- Tail concentration HHI
- 單檔半砍 50% 後 ES95 改善量

寫入：
- stock_meta["__synthetic_portfolio_risk__"]["component_tail_risk"]

v0.6 新增：
- inverse-vol baseline
- dependency-free HRP-lite
- EWMA covariance risk budgeting
- current vs HRP-lite suggested weight
- current risk contribution vs HRP-lite risk contribution
- HRP-lite ordering

寫入：
- stock_meta["__synthetic_portfolio_risk__"]["risk_budgeting"]

前端新增：
- v0.5 尾部風險歸因面板
- Component ES 95 Top 12
- v0.6 HRP-lite 風險預算差異表
- v0.5 / v0.6 方法限制

注意：
- HRP-lite 是無外部套件初版，不是完整 Riskfolio-Lib / skfolio。
- Component VaR 是歷史 VaR 門檻附近樣本近似。
- Component ES 是較可靠的尾部歸因主指標。
- 半砍改善量假設減掉的部位停在現金，不重新配置到其他風險資產。

已檢查：
- python -m py_compile scripts/update_stock_meta.py
- python -m py_compile update_stock_meta.py
- node --check assets/js/app.bundle.js

使用方式：
1. 將 zip 內檔案照原路徑 upload 覆蓋到 GitHub。
2. commit。
3. 跑 Actions → Update Stock Quant Meta。
4. 等 GitHub Pages 部署。
5. Ctrl + F5。

預期 log：
OK synthetic risk: status=OK, confidence=..., strict_sample=..., flexible_sample=..., usable_weight=...%, quantstats=OK, ewma_regime=OK, component_tail=OK, risk_budgeting=OK
