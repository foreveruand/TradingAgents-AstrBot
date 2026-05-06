"""
市场分析师 - 负责技术面分析
"""


from astrbot.api import logger

from ..personas import PERSONA_MARKET_ANALYST
from .base import BaseAnalyst


class MarketAnalyst(BaseAnalyst):
    """市场分析师 - 复刻原始项目的市场分析师角色"""

    def __init__(self, llm, data_fetcher):
        super().__init__(llm, data_fetcher)

    def _get_persona_id(self, *, is_etf: bool = False) -> str:
        return PERSONA_MARKET_ANALYST

    async def analyze(self, ticker: str, trade_date: str) -> str:
        """执行市场分析（自行获取数据）"""
        market_info, normalized_ticker, stock_name = self._resolve_ticker_info(ticker)
        logger.info(f"市场分析师开始分析: {ticker}")

        market_data = await self.data_fetcher.get_market_data(
            normalized_ticker, trade_date
        )

        prompt = self._build_analysis_prompt(
            ticker=normalized_ticker,
            trade_date=trade_date,
            market_info=market_info,
            market_data=market_data,
            extra_context=self._get_extra_context(
                stock_name, normalized_ticker, market_info
            ),
        )

        report = await self._call_llm(prompt, persona_id=self._get_persona_id())
        logger.info(f"市场分析师完成分析: {ticker}, 报告长度: {len(report)}")
        return report

    async def analyze_with_data(
        self, ticker: str, trade_date: str, market_data_raw: str
    ) -> str:
        """使用预获取的市场数据执行分析"""
        market_info, normalized_ticker, stock_name = self._resolve_ticker_info(ticker)
        logger.info(f"市场分析师开始分析（预取数据）: {ticker}")

        prompt = self._build_analysis_prompt(
            ticker=normalized_ticker,
            trade_date=trade_date,
            market_info=market_info,
            market_data=market_data_raw,
            extra_context=self._get_extra_context(
                stock_name, normalized_ticker, market_info
            ),
        )

        report = await self._call_llm(prompt, persona_id=self._get_persona_id())
        logger.info(f"市场分析师完成分析: {ticker}, 报告长度: {len(report)}")
        return report

    def _get_extra_context(
        self, stock_name: str, ticker: str, market_info: dict
    ) -> str:
        """获取额外上下文"""
        return f"""## 分析要求
请重点关注 {stock_name}（{ticker}）的技术面分析要点：

1. **价格走势**：判断当前趋势（上升/下降/盘整）
2. **成交量配合**：分析成交量与价格走势的关系
3. **均线系统**：分析不同周期均线的交叉和排列
4. **技术指标**：MACD、KDJ、RSI等指标的信号
5. **支撑压力**：识别关键的支撑位和压力位

## 市场特点
- 市场类型：{market_info["market_name"]}
- 货币单位：{market_info["currency_name"]}（{market_info["currency_symbol"]}）

请基于上述数据，进行专业的技术面分析。
"""
