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

1. **时效性评估**：新闻发布时间距现在多久
2. **影响力评估**：新闻对股价的潜在影响程度
3. **利好/利空判断**：明确标注利好和利空因素
4. **情绪变化**：分析新闻导致的投资者情绪变化
5. **历史类比**：与历史类似新闻的市场反应对比

## 市场特点
- 市场类型：{market_info["market_name"]}
- 货币单位：{market_info["currency_name"]}（{market_info["currency_symbol"]}）

请基于上述数据，进行专业的新闻面分析。
"""
