# 응답 메모

- 데이터 출처가 공식 API가 아니라 공개 Naver Finance/Npay Stock web page와 undocumented web endpoint임을 분명히 합니다.
- 가격 데이터에는 값이 있으면 `localTradedAt`, market status, response timestamp를 함께 표시합니다.
- 홈/NXT 데이터에는 `nxtMarketStatus`와 `nxtOverMarketPriceInfo`가 있으면 보존합니다. NXT ranking은 아직 PC HTML 기반이라 컬럼과 장상태 label이 바뀔 수 있으므로 현재 화면/traffic 재검증이 필요합니다.
- 지수 quote는 `SERVICE_INDEX` area의 `time`, `ms`, `cd`, `nv`, `cv`, `cr`를 함께 보존합니다.
- `PREOPEN`, `TRADING`, `UNCHANGED` 같은 Naver status 문자열은 보존합니다. 필요할 때만 짧은 한국어/영어 설명을 덧붙입니다.
- mobile integration payload는 전체 dump를 피하고 `totalInfos`, `dealTrendInfos`, `researches`, `industryCompareInfo`, `consensusInfo`, `irScheduleInfo`를 나누어 요약합니다.
- PC table page에서는 spacer row와 의미 있는 cell이 없는 row를 건너뜁니다.
- Wisereport는 회사와 회계 기준에 따라 table 구조가 달라지므로 화면에 표시된 label을 유지합니다.
- Naver AI briefing이나 news snippet을 검증된 사실처럼 표현하지 않습니다. Naver가 제공한 content임을 식별합니다.
