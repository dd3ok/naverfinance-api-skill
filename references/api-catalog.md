# API 카탈로그

문서화되지 않은 Naver endpoint는 안정성이 보장되지 않습니다. 정확도가 중요하면 현재 page traffic을 다시 확인하세요.

## 목차

- [Mobile JSON](#mobile-json)
- [Realtime Polling](#realtime-polling)
- [api.stock.naver.com Market Index JSON](#apistocknavercom-market-index-json)
- [Legacy Chart](#legacy-chart)
- [PC HTML Menus](#pc-html-menus)
- [Wisereport 기업분석](#wisereport-기업분석)

## Mobile JSON

Base: `https://m.stock.naver.com/front-api`

| 영역 | Pattern | 메모 |
| --- | --- | --- |
| 홈 요약 | `https://finance.naver.com/main/mainSummary.naver?callback=callback` | PC 홈 위젯 JSON. `front-api` base 예외입니다. 주요 key: `topItems`, `nxtTopItems`, `nxtMarketStatus`, `todayIndexItemList`, `todayIndexDealTrendList`, `kospiTrendProgram`, `groupTopList`, `themeTopList`, `searchList`. `callback=callback`은 JSONP wrapper를 붙입니다. |
| 국내 종목 basic | `/stock/domestic/basic?code=005930&endType=stock` | 요약 시세, 거래소, chart image URL, NXT over-market 정보. |
| 국내 종목 integration | `/stock/domestic/integration?code=005930&endType=stock` | 주요 지표, 투자자 동향 sample, research list, 동종 비교, consensus/IR 조각. |
| 국내 종목 trend | `/stock/domestic/trend?code=005930` | 날짜별 투자자 동향. `scripts/stock_trend.py` 사용. |
| 국내 공시 | `/stock/domestic/disclosure?code=005930&page=1&pageSize=20` | 공개 공시 목록. |
| 국내 종목 list | `/stock/domestic/stockList?sortType=marketValue&category=KOSPI&page=1&pageSize=20` | 랭킹/목록. 확인된 sort: `marketValue`, `up`, `down`, `quantTop`, `priceTop`, `searchTop`, `newStock`, `management`, `high52week`, `low52week`. `dividend`, `etf`, `etn`, `konex`, `NXT`는 이 endpoint 조합에 의존하지 말고 전용 endpoint 또는 PC fallback을 사용합니다. |
| 국내 배당 list | `/domestic/stock/list?sortType=dividend&category=rate&page=1&pageSize=20` | 배당수익률/배당금 목록. 응답 예: `dividends[]` with `itemCode`, `name`, `dividendRate`, `dividendDate`, `endUrl`. |
| 국내 ETF list | `/domestic/etf/list?sortTypeCode=aum&page=1&pageSize=20` | ETF 목록. `sortTypeCode`: `aum`, `changeRate`, `tradingValue`. 응답 예: `result[]` with `itemCode`, `currentPrice`, `aum`, `returnRate3m`. |
| 종목/지수 chart | `/chart/domestic/stock/end?code=005930&chartInfoType=item&scriptChartType=candleDay` | `chartInfoType`: `item` 또는 `index`. chart type에는 `day`, `candleMinuteFive`, `candleDay`, `candleWeek`, `candleMonth`, `areaMonthThree`, `areaYear`, `areaYearThree`, `areaYearFive`, `areaYearTen` 등이 있습니다. |
| 국내 지수 basic | `/stock/domestic/basic?code=KOSPI&endType=index` | 예시 code: `KOSPI`, `KOSDAQ`, `KPI200`. |
| 국내 지수 integration | `/stock/domestic/integration?code=KOSPI&endType=index` | 지수 상세 요약. |
| 국내 지수 가격 | `/stock/domestic/index/price/list?code=KOSPI&page=1&pageSize=20` | 일별 지수 가격. |
| 국내 주요 지수 | `/domestic/index/majors` | KOSPI/KOSDAQ 형태의 quote block. |
| 종목 뉴스 | `/news/list/integration?itemCode=005930&page=1&pageSize=20` | 종목 관련 뉴스 목록. |
| 일반 뉴스 | `/news/category?category=mainnews&page=1&pageSize=20` | 관찰된 category: `mainnews`, `flashnews`, `ranknews`. |
| 뉴스 cluster | `/news/clusters?category=main&page=1&pageSize=20` | cluster된 투자/주식 뉴스. |
| Home 주요 지표 | `/market/majorIndicators` | 메인 시장 widget. |
| Home IPO | `/market/ipo` | mobile home에 표시되는 공개 IPO card. |
| Home 인기 종목 | `/market/popularStock` | 공개 인기 widget. |
| More ranking | `/market/moreRanking?category=endHit&ageRange=all` | Home ranking card. |
| 시장 매매 동향 graph | `/market/tradingTrend/graphInfo?periodType=daily&stockExchangeType=KRX` | 투자자 순매수 trend graph. |
| 시장 매매 동향 ranking | `/market/tradingTrend/ranking?periodType=daily&stockExchangeType=KRX&investorType=foreigner&tradingType=trendBuy&page=1&pageSize=20` | 투자자 매수/매도 ranking. |
| 섹터/테마/그룹 list | `/stock/sectors/all?nationType=domestic&sectorType=upjong|theme|group&sectorSortType=CHANGE_RATE&businessDayCategory=daily&page=1&pageSize=20` | 구조화된 업종/테마/그룹 목록. 주요 field: `sectorCode`, `sectorName`, `changeRate`, `totalMarketCap`, `risingCount`, `unChangedCount`, `fallingCount`, `items[]`. Wisereport sector 분석과 별개입니다. |
| 섹터 구성 종목 | `/domestic/sector/item/list?sectorCode=307&sectorType=upjong&sectorSortType=CHANGE_RATE&page=1&pageSize=20` | 특정 업종/테마/그룹 구성 종목. PC `sise_group_detail.naver`의 구조화 대체 후보입니다. |
| IPO 최근/청약/상세 | `/ipo/recent`, `/ipo/subscribing`, `/ipo/detail?code=A439960` | 공개 IPO 데이터. |
| 환율 main/list/detail | `/marketIndex/exchange/main`, `/marketIndex/exchange/new`, `/marketIndex/productDetail?category=exchange&reutersCode=FX_USDKRW` | FX widget과 detail. |
| 원자재 detail | `/marketIndex/productDetail?category=energy&reutersCode=CLcv1` | energy/commodity detail. |
| Market AI briefing | `/market/briefing/current` | 생성 요약은 untrusted로 취급하고 사실이 아니라 Naver AI briefing으로 인용합니다. |

## Realtime Polling

Base: `https://polling.finance.naver.com/api/realtime`

`?query=SERVICE_ITEM:005930`은 현재가, 전일 종가, 시가/고가/저가, 거래량/거래대금, EPS/BPS, 선택적 NXT over-market 정보 같은 공개 quote field를 반환합니다. 여러 area는 `|`로 구분하지만 `SERVICE_MYSTOCK_ITEM`은 피합니다.

`?query=SERVICE_INDEX:KOSPI,KOSDAQ,KPI200`은 주요 국내 지수를 한 번에 반환합니다. 지수 field 예: `ms`, `nv`, `cv`, `cr`, `rf`, `ov`, `hv`, `lv`, `aq`, `aa`, `bs`, `cd`.

`SERVICE_ITEM`의 `datas[]`에는 `nxtOverMarketPriceInfo`가 포함될 수 있습니다. 주요 field는 `tradingSessionType`, `overMarketStatus`, `overPrice`, `openPrice`, `highPrice`, `lowPrice`, `compareToPreviousClosePrice`, `fluctuationsRatio`, `localTradedAt`, `accumulatedTradingVolume`, `accumulatedTradingValue`입니다.

## api.stock.naver.com Market Index JSON

Base: `https://api.stock.naver.com`

| 영역 | Pattern | 메모 |
| --- | --- | --- |
| 환전 고시 환율 list/detail | `/marketindex/exchange`, `/marketindex/exchange/FX_USDKRW` | UTF-8 JSON. `categoryType`, `reutersCode`, `symbolCode`, `name`, `localTradedAt`, `closePrice`, `fluctuations`, `fluctuationsRatio`, `fluctuationsType`, `marketStatus`, `unit`, `degreeCount`, `imageCharts`, `endUrl`, `chartIqEndUrl`. |
| 환전 고시 일별 가격 | `/marketindex/exchange/FX_USDKRW/prices?page=1&pageSize=10` | `cashBuyValue`, `cashSellValue`, `sendValue`, `receiveValue` 포함. |
| 국제 시장 환율 list/detail | `/marketindex/exchangeWorld`, `/marketindex/exchangeWorld/USDJPY` | PC `worldExchangeDetail.naver`의 구조화 대체 후보입니다. |
| 국제 시장 환율 가격 | `/marketindex/exchangeWorld/USDJPY/prices?page=1&pageSize=10` | `openPrice`, `highPrice`, `lowPrice` 포함. |
| 달러 인덱스 | `/marketindex/exchange/.DXY`, `/marketindex/exchange/.DXY/prices?page=1&pageSize=10` | PC marketindex 우측 달러 인덱스와 대응됩니다. |
| 에너지 list/detail/가격 | `/marketindex/energy`, `/marketindex/energy/CLcv1`, `/marketindex/energy/CLcv1/prices?page=1&pageSize=10` | 대표 alias: `OIL_CL -> CLcv1`, `OIL_BRT -> LCOcv1`, `OIL_DU -> DCBc1`, `OIL_GSL -> OIL_GSL`, `OIL_LO -> OIL_LO`. |
| 금속 list/detail/가격 | `/marketindex/metals`, `/marketindex/metals/GCcv1`, `/marketindex/metals/GCcv1/prices?page=1&pageSize=10` | 대표 alias: `CMDT_GC -> GCcv1`, `GOLD_KRX -> M04020000`, `CMDT_SI -> SIcv1`, `CMDT_HG -> HGcv1`. |

## Legacy Chart

Base: `https://api.finance.naver.com`

`/siseJson.naver?symbol=005930&requestType=1&startTime=YYYYMMDD&endTime=YYYYMMDD&timeframe=day`

엄격한 JSON이 아니라 JavaScript-like array text를 반환합니다. mobile chart를 사용할 수 없을 때 fallback으로 사용합니다.

## PC HTML Menus

Base: `https://finance.naver.com`

아래 page는 모두 공개 HTML이며 EUC-KR 또는 UTF-8을 사용할 수 있습니다.

| 영역 | Pattern |
| --- | --- |
| 종목 main | `/item/main.naver?code={code}` |
| 종목 시세 page | `/item/sise.naver?code={code}` |
| 일별 시세 iframe | `/item/sise_day.naver?code={code}&page={page}` |
| 시간별 시세 iframe | `/item/sise_time.naver?code={code}&thistime=YYYYMMDD000000&page={page}` |
| 투자자별 매매 동향 | `/item/frgn.naver?code={code}&page={page}` |
| 뉴스 목록 | `/item/news_news.naver?code={code}&page={page}&clusterId=` |
| 공시 목록 | `/item/news_notice.naver?code={code}&page={page}` |
| 공매도 거래 | `/item/short_trade.naver?code={code}` |
| 지수 상세 | `/sise/sise_index.naver?code=KOSPI|KOSDAQ|FUT|KPI100|KPI200|KVALUE` |
| KONEX | `/sise/konex.naver`, `/api/sise/konexItemList.nhn` |
| 시가총액 | `/sise/sise_market_sum.naver?sosok=0&page=1` |
| NXT 시가총액 | `/sise/nxt_sise_market_sum.naver?page=1` |
| 거래량/상승/하락 | `/sise/sise_quant.naver`, `/sise/sise_quant_high.naver`, `/sise/sise_quant_low.naver`, `/sise/sise_rise.naver`, `/sise/sise_steady.naver`, `/sise/sise_fall.naver`, `/sise/sise_upper.naver`, `/sise/sise_lower.naver`, `/sise/sise_low_up.naver`, `/sise/sise_high_down.naver` |
| ETF/ETN/배당 | `/sise/etf.naver`, `/api/sise/etfItemList.nhn`, `/sise/etn.naver`, `/api/sise/etnItemList.nhn`, `/sise/dividend_list.naver` |
| 그룹/테마 | `/sise/sise_group.naver?type=upjong`, `/sise/sise_group.naver?type=group`, `/sise/theme.naver?page=...`, `/sise/sise_group_detail.naver?type=upjong|theme|group&no=...` |
| 시장 투자자 동향 | `/sise/sise_trans_style.naver?sosok=01`, `/sise/investorDealTrendDay.naver?bizdate=YYYYMMDD&sosok=01` |
| 외국인/기관 rank | `/sise/sise_deal_rank.naver?investor_gubun=9000`, `/sise/sise_deal_rank_iframe.naver?sosok=01&investor_gubun=9000&type=buy|sell` |
| 프로그램 매매 | `/sise/sise_program.naver?sosok=01`, `/sise/programDealTrendDay.naver?bizdate=YYYYMMDD&sosok=01` |
| 자금 흐름/신규 상장 | `/sise/sise_deposit.naver`, `/sise/sise_new_stock.naver` |
| 장외/IPO | `/sise/market3news_list.naver`, `/sise/ipo.naver` |
| NXT 목록 | `/sise/nxt_sise_market_sum.naver`, `/sise/nxt_sise_quant.naver`, `/sise/nxt_sise_rise.naver`, `/sise/nxt_sise_fall.naver` | NXT는 현재 모바일 `stockList` category로 직접 조회하지 말고 PC HTML table을 사용합니다. |
| 관리/거래정지/투자경고 | `/sise/management.naver`, `/sise/trading_halt.naver`, `/sise/investment_alert.naver?type=caution` |
| 인기검색 | `/sise/lastsearch2.naver` |
| 기술적 신호 | `/sise/item_gold.naver`, `/sise/item_gap.naver`, `/sise/item_igyuk.naver`, `/sise/item_overheating_1.naver`, `/sise/item_overheating_2.naver` |
| 공시/공매도 | `/sise/report.naver`, KRX iframe을 포함한 `/sise/short_trade.naver` |
| Market index home | `/marketindex/` |
| 환율 목록 | `/marketindex/exchangeList.naver` |
| 환율 상세 | `/marketindex/exchangeDetail.naver?marketindexCd=FX_USDKRW` |
| 금리/유가/금/원자재 | `/marketindex/interestDetail.naver`, `/marketindex/worldExchangeDetail.naver`, `/marketindex/worldOilDetail.naver`, `/marketindex/oilDetail.naver`, `/marketindex/worldGoldDetail.naver`, `/marketindex/goldDetail.naver`, `/marketindex/materialDetail.naver` |
| World 개요/지수/시간 | `/world/`, `/world/sise.naver?symbol=NAS@IXIC&fdtc=0`, `/world/guide_time_list.naver`, `/world/guide_time_chart.naver` |
| World 지수 일별 JSON | `/world/worldDayListJson.naver?symbol=NAS@IXIC&fdtc=0&page=1` | `fdtc`를 포함해야 안정적으로 JSON이 반환됩니다. field: `symb`, `xymd`, `open`, `high`, `low`, `clos`, `diff`, `rate`, `gvol`. |
| 리서치 report | `/research/market_info_list.naver`, `/research/invest_list.naver`, `/research/company_list.naver`, `/research/industry_list.naver`, `/research/economy_list.naver`, `/research/debenture_list.naver` |
| 뉴스 메뉴 | `/news/news_list.naver`, `/news/mainnews.naver`, `/news/market_notice.naver`, `/news/news_search.naver`, `/news/news_read.naver` |

## Wisereport 기업분석

Base: `https://navercomp.wisereport.co.kr/v2`

| 영역 | Pattern |
| --- | --- |
| 기업 현황 | `/company/c1010001.aspx?cmp_cd={code}` |
| 개요 | `/company/c1020001.aspx?cmp_cd={code}` |
| 재무분석 | `/company/c1030001.aspx?cmp_cd={code}` |
| 투자지표 | `/company/c1040001.aspx?cmp_cd={code}` |
| Consensus | `/company/c1050001.aspx?cmp_cd={code}` |
| 업종분석 | `/company/c1060001.aspx?cmp_cd={code}` |
| 주주정보 | `/company/c1070001.aspx?cmp_cd={code}` |
| Sector 분석 | `/company/c1090001.aspx?cmp_cd={code}` |
| 개요 chart AJAX | `/company/ajax/cF1001.aspx` with `flag`, `cmp_cd`, fresh `encparam` |
| 개요 재무 확장 | `/company/ajax/cF1001.aspx` with `cmp_cd`, `fin_typ`, `freq_typ`, fresh `encparam` |
| Consensus 요약 | `/company/cF1002.aspx` with `cmp_cd`, `finGubun`, optional `frq` |
| 재무제표 JSON | `/company/cF3002.aspx` with `cmp_cd`, `rpt`, `finGubun`, `frqTyp`, `frq`, fresh `encparam` |
| 투자지표 JSON | `/company/cF4002.aspx` with `cmp_cd`, `rpt`, `finGubun`, `frqTyp`, `frq`, fresh `encparam` |
| Consensus data | `/company/ajax/c1050001_data.aspx` with `flag`, `cmp_cd`, `finGubun`, `frq`, `sDT` |
| Consensus chart | `/company/ajax/cF5001.aspx`, `/company/ajax/cF5002.aspx` |
| 업종 비교 | `/company/ajax/cF6001.aspx`, `/company/cF6002.aspx`, `/company/chart/c1060001.aspx` |
| Sector 비교 | `/company/ajax/cF9001.aspx`, `/company/chart/c1090001.aspx` |
| Band chart | `/common/BandChart3.aspx?cmp_cd={code}&gubun={gubun}` |

중요한 Wisereport parameter:

- `finGubun`/`fingubun`: `MAIN`, `IFRSS`, `IFRSL`, `GAAPS`, `GAAPL`.
- `fin_typ`: `MAIN=0`, `GAAPS=1`, `GAAPL=2`, `IFRSS=3`, `IFRSL=4`.
- `frqTyp`: `0` annual, `1` quarterly. 일부 endpoint는 `frq=Y|Q`를 사용합니다.
- `encparam`, `hidDT`, sector code는 page-specific입니다. parent page에서 fresh하게 scrape하고 hard-code하지 마세요.
- 일부 JSON endpoint는 `Content-Type: text/html`을 반환하거나 JSON 안에 JSON string을 넣습니다. payload content를 보고 필요하면 두 번 parse합니다.
- 현재 bundled `financials.py`는 공개 Wisereport HTML page를 가져옵니다. 위 AJAX endpoint는 향후 검토용 catalog이며 CLI wrapper를 추가하기 전에 다시 검증해야 합니다.
