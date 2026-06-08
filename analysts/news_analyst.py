"""
新闻分析师 - 负责消息面分析
"""

from astrbot.api import logger

from ..personas import PERSONA_NEWS_ANALYST
from .base import BaseAnalyst


class NewsAnalyst(BaseAnalyst):
    """新闻分析师 - 复刻原始项目的新闻分析师角色"""

    def __init__(self, llm, data_fetcher):
        super().__init__(llm, data_fetcher)

    def _get_persona_id(self, *, is_etf: bool = False) -> str:
        return PERSONA_NEWS_ANALYST

    async def analyze(self, ticker: str, trade_date: str) -> str:
        """执行新闻分析（自行获取数据）"""
        market_info, normalized_ticker, stock_name = self._resolve_ticker_info(ticker)
        logger.info(f"新闻分析师开始分析: {ticker}")

        news_data = await self.data_fetcher.get_news(normalized_ticker, trade_date)
        sentiment_data = await self.data_fetcher.get_sentiment(
            normalized_ticker, trade_date
        )

        prompt = self._build_analysis_prompt(
            ticker=normalized_ticker,
            trade_date=trade_date,
            market_info=market_info,
            news_data=news_data,
            sentiment_data=sentiment_data,
            extra_context=self._get_extra_context(
                stock_name, normalized_ticker, market_info
            ),
        )

        report = await self._call_llm(prompt, persona_id=self._get_persona_id())
        logger.info(f"新闻分析师完成分析: {ticker}, 报告长度: {len(report)}")
        return report

    async def analyze_with_data(
        self, ticker: str, trade_date: str, news_data_raw: str, sentiment_data_raw: str
    ) -> str:
        """使用预获取的新闻和情绪数据执行分析"""
        market_info, normalized_ticker, stock_name = self._resolve_ticker_info(ticker)
        logger.info(f"新闻分析师开始分析（预取数据）: {ticker}")

        prompt = self._build_analysis_prompt(
            ticker=normalized_ticker,
            trade_date=trade_date,
            market_info=market_info,
            news_data=news_data_raw,
            sentiment_data=sentiment_data_raw,
            extra_context=self._get_extra_context(
                stock_name, normalized_ticker, market_info
            ),
        )

        report = await self._call_llm(prompt, persona_id=self._get_persona_id())
        logger.info(f"新闻分析师完成分析: {ticker}, 报告长度: {len(report)}")
        return report

    def _get_extra_context(
        self, stock_name: str, ticker: str, market_info: dict
    ) -> str:
        """获取额外上下文"""
        return f"""## 分析要求
请重点关注 {stock_name}（{ticker}）的新闻面分析要点：

1. **时效性评估**：按24小时内、近一周、近一月、历史背景分层，旧闻不得当作新催化。
2. **来源可信度**：优先使用公告、财报、监管信息、主流财经媒体；传闻、论坛情绪和未证实消息必须降权。
3. **影响链条**：说明事件如何影响收入、成本、利润率、估值、资金偏好、监管预期或风险溢价。
4. **利好/利空判断**：明确标注短期情绪影响和中长期基本面影响，不把一次性情绪当长期趋势。
5. **市场预期差**：判断消息是否已经被价格反映，结合近期涨跌和量能说明追涨/杀跌风险。
6. **事件跟踪点**：列出后续最需要验证的公告、业绩指标、监管进展或行业数据。

## 市场特点
- 市场类型：{market_info["market_name"]}
- 货币单位：{market_info["currency_name"]}（{market_info["currency_symbol"]}）

请基于上述数据，输出事件驱动分析，避免复述新闻标题。
"""
