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

1. **多周期趋势**：优先使用日线/周线/月线摘要，判断趋势共振、背离或震荡；不要只凭最新一天涨跌下结论。
2. **均线系统**：判断短中长期均线是多头排列、空头排列还是缠绕，并说明当前价与关键均线的距离。
3. **量价关系**：识别放量突破、缩量回踩、放量下跌、缩量反弹；量能不足时降低突破或反转结论强度。
4. **动量指标**：结合MACD、KDJ、RSI解释动量强弱、超买超卖、背离和假信号；数据缺失时不要编造指标值。
5. **支撑压力**：从近期高低点、均线、整数关口和成交密集区提炼1-2个最关键价位。
6. **交易计划**：给出短线/波段的观察位、确认位、失效位、止损参考和风险收益比是否值得。

## 技术结论分级
- 强多：趋势、量能、动量至少两项共振，并且价格站上关键压力或均线。
- 偏多：趋势改善但量能或动量仍需确认，只能给观察/轻仓试探建议。
- 中性：多周期冲突或均线缠绕，以区间交易和等待突破为主。
- 偏空：跌破关键支撑、均线空头或放量下跌至少满足两项。
- 强空：趋势、量能、动量共同转弱，并且反弹无法收复关键位。

## 市场特点
- 市场类型：{market_info["market_name"]}
- 货币单位：{market_info["currency_name"]}（{market_info["currency_symbol"]}）

请基于上述数据，输出直接服务于决策的技术面分析，不要堆砌指标定义。
"""
