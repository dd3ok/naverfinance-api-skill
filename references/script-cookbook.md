# Script Cookbook

## 자주 쓰는 조회

```bash
python3 scripts/home.py --limit 5
python3 scripts/stock_summary.py --code 005930
python3 scripts/quote.py --code 005930 --code 000660
python3 scripts/quote.py --index KOSPI --index KOSDAQ --index KPI200
python3 scripts/stock_chart.py --code 005930 --period day --start 20260420 --end 20260427
python3 scripts/stock_trend.py --code 005930 --limit 10
python3 scripts/news.py --code 005930 --kind stock --limit 5
python3 scripts/market_ranking.py --kind market-cap --market kospi --page 1 --limit 10
python3 scripts/market_ranking.py --kind konex --page 1 --limit 10
python3 scripts/market_ranking.py --kind upjong --page 1 --limit 10
python3 scripts/market_ranking.py --kind upjong --detail-no 264 --limit 10
python3 scripts/market_ranking.py --kind theme --page 2 --limit 10
python3 scripts/market_ranking.py --kind theme --detail-no 318 --limit 10
python3 scripts/market_ranking.py --kind group --page 1 --limit 10
python3 scripts/market_ranking.py --kind etf --page 1 --limit 10
python3 scripts/market_ranking.py --kind etn --page 1 --limit 10
python3 scripts/market_ranking.py --kind low-up --limit 10
python3 scripts/market_ranking.py --kind quant-high --limit 10
python3 scripts/market_ranking.py --kind investor-trend --market kospi --limit 10
python3 scripts/market_ranking.py --kind foreign-buy --market kospi --limit 10
python3 scripts/market_ranking.py --kind program-trend --market kospi --limit 10
python3 scripts/market_ranking.py --kind nxt-market-cap --limit 10
python3 scripts/market_ranking.py --kind popular-search --limit 10
python3 scripts/market_ranking.py --kind golden-cross --limit 10
python3 scripts/market_ranking.py --kind report
python3 scripts/market_ranking.py --kind short-trade
python3 scripts/indices.py --code KOSPI --include-chart --period day --start 20260420 --end 20260427
python3 scripts/indices.py --code KVALUE
python3 scripts/indices.py --code FX_USDKRW --limit 3
python3 scripts/indices.py --code FX_USDJPY --limit 3
python3 scripts/indices.py --code IRR_CD91 --limit 3
python3 scripts/indices.py --code CMDT_GC --limit 3
python3 scripts/indices.py --code GOLD_KRX --limit 3
python3 scripts/world.py --kind overview --limit 5
python3 scripts/world.py --kind index --symbol nasdaq --limit 5
python3 scripts/world.py --kind prices --symbol nasdaq --limit 5
python3 scripts/world.py --kind hours --limit 10
python3 scripts/marketindex.py --kind overview --limit 5
python3 scripts/marketindex.py --kind exchange-list --limit 10
python3 scripts/marketindex.py --kind detail --code FX_USDKRW --limit 3
python3 scripts/marketindex.py --kind api-detail --code FX_USDKRW
python3 scripts/marketindex.py --kind api-prices --code FX_USDKRW --limit 3
python3 scripts/marketindex.py --kind api-prices --code FX_USDJPY --limit 3
python3 scripts/marketindex.py --kind api-prices --code OIL_CL --limit 3
python3 scripts/marketindex.py --kind api-prices --code CMDT_GC --limit 3
python3 scripts/research.py --kind company --page 1 --limit 10
python3 scripts/research.py --kind economy --page 1 --limit 10
python3 scripts/news.py --kind flash --page 1 --limit 10
python3 scripts/news.py --kind main --page 1 --limit 10
python3 scripts/news.py --kind notice --page 1 --limit 10
python3 scripts/news.py --kind search --query 삼성전자 --page 1 --limit 10
python3 scripts/financials.py --code 005930 --kind overview
```

## 출력

모든 스크립트는 기본적으로 JSON을 출력합니다. 파일로 저장하려면 `--output path.json`을 사용합니다.

PC HTML table 기반 출력은 공개 page 구조를 best-effort로 평탄화합니다. `marketindex.py --kind exchange-list`처럼 grouped header, 중복 header, iframe table이 섞인 page는 현재 화면과 함께 재확인하고, 정확한 column 의미가 중요하면 원본 page traffic/table 구조를 다시 점검하세요.

## Market Ranking Kind

`konex`, `market-cap`, `volume`, `quant-high`, `quant-low`, `rise`, `fall`, `steady`, `upper`, `lower`, `low-up`, `high-down`, `etf`, `etn`, `dividend`, `foreign-hold`, `theme`, `upjong`, `group`, `investor-trend`, `foreign-buy`, `foreign-sell`, `institution-buy`, `institution-sell`, `program-trend`, `deposit`, `new-stock`, `market3`, `ipo`, `nxt-market-cap`, `nxt-volume`, `nxt-rise`, `nxt-fall`, `management`, `trading-halt`, `investment-alert`, `popular-search`, `golden-cross`, `gap-up`, `disparity-overheat`, `sentiment-overheat`, `relative-strength-overheat`, `report`, `short-trade`.

목록 page에는 `--page N`을 사용합니다. `theme`, `upjong`, `group`의 목록 row에는 `detailNo`와 `detailUrl`이 들어 있습니다. 같은 `--kind`와 함께 `--detail-no <no>`를 넘기면 `sise_group_detail.naver`에서 관련 종목을 조회합니다.

`upjong`, `theme`, `group` 목록은 가능하면 mobile sector JSON을 우선 사용하고, 실패하면 PC HTML로 fallback합니다. `dividend`는 `/front-api/domestic/stock/list?sortType=dividend&category=rate`, `etf`는 `/front-api/domestic/etf/list?sortTypeCode=aum`을 우선 사용합니다. `etn`, `konex`, `NXT` 목록은 기존 PC JSON/HTML 경로를 유지합니다.

`report`는 공개 공시 tab link를 반환합니다. `short-trade`는 Naver page 안에 embedded된 KRX iframe URL을 반환합니다. 상세 공매도 표가 page 내부 KRX iframe에서 제공되기 때문입니다.

## World, Market Index, Research, News

- `world.py --kind overview|index|prices|hours`; 자주 쓰는 symbol은 `nasdaq`, `dow`, `sp500`, `nikkei225` 또는 `NAS@IXIC` 같은 원본 symbol입니다. `prices`는 `worldDayListJson`을 사용합니다.
- `marketindex.py --kind overview|exchange-list|detail|api-detail|api-prices`; `detail` code에는 `FX_USDKRW`, `FX_USDJPY`, `FX_USDX`, `OIL_CL`, `OIL_GSL`, `CMDT_GC`, `GOLD_KRX`, `IRR_CD91` 등 Naver marketindex code가 들어갑니다. `api-*`는 `api.stock.naver.com/marketindex` JSON을 사용하며 `FX_*`, `FX_USDX`, `OIL_CL`, `OIL_BRT`, `OIL_DU`, `OIL_GSL`, `OIL_LO`, `CMDT_GC`, `GOLD_KRX` 등 확인된 exchange/exchangeWorld/energy/metals code에 맞춰져 있습니다. `IRR_*` 금리는 아직 PC detail route를 사용하세요.
- `research.py --kind market-info|invest|company|industry|economy|debenture`.
- `news.py --kind flash|main|market|analysis|world|bond|memo|fx|rank|photo|tv|notice|search`; `stock`과 `disclosure`는 `--code`가 필요하고, `search`는 `--query`가 필요합니다.

## 날짜 형식

- Mobile chart endpoint는 `YYYYMMDD0000`을 사용합니다.
- Legacy `siseJson`은 `YYYYMMDD`를 사용합니다.
- Bundled chart CLI는 날짜 인자를 `YYYYMMDD`로 받습니다.
- PC page는 날짜를 `YYYY.MM.DD`로 표시하는 경우가 많습니다.
