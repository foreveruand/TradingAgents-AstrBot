"""
基本面分析师 - 负责基本面分析
"""


from astrbot.api import logger

from ..personas import (
    PERSONA_FUNDAMENTALS_ANALYST,
    PERSONA_FUNDAMENTALS_ETF_ANALYST,
)
from .base import BaseAnalyst


class FundamentalsAnalyst(BaseAnalyst):
    """基本面分析师 - 复刻原始项目的基本面分析师角色"""

    def __init__(self, llm, data_fetcher):
        super().__init__(llm, data_fetcher)

    def _get_persona_id(self, *, is_etf: bool = False) -> str:
        if is_etf:
            return PERSONA_FUNDAMENTALS_ETF_ANALYST
        return PERSONA_FUNDAMENTALS_ANALYST

    async def analyze(self, ticker: str, trade_date: str) -> str:
        """执行基本面分析（自行获取数据）"""
        market_info, normalized_ticker, stock_name = self._resolve_ticker_info(ticker)
        logger.info(f"基本面分析师开始分析: {ticker}")

        fundamentals_data = await self.data_fetcher.get_fundamentals(
            normalized_ticker, trade_date
        )

        is_etf = market_info.get("is_etf", False)
        prompt = self._build_analysis_prompt(
            ticker=normalized_ticker,
            trade_date=trade_date,
            market_info=market_info,
            fundamentals_data=fundamentals_data,
            extra_context=self._get_extra_context(
                stock_name, normalized_ticker, market_info
            ),
            is_etf=is_etf,
        )

        report = await self._call_llm(
            prompt,
            persona_id=self._get_persona_id(is_etf=is_etf),
        )
        logger.info(f"基本面分析师完成分析: {ticker}, 报告长度: {len(report)}")
        return report

    async def analyze_with_data(
        self, ticker: str, trade_date: str, fundamentals_data_raw: str
    ) -> str:
        """使用预获取的基本面数据执行分析"""
        market_info, normalized_ticker, stock_name = self._resolve_ticker_info(ticker)
        logger.info(f"基本面分析师开始分析（预取数据）: {ticker}")

        is_etf = market_info.get("is_etf", False)
        prompt = self._build_analysis_prompt(
            ticker=normalized_ticker,
            trade_date=trade_date,
            market_info=market_info,
            fundamentals_data=fundamentals_data_raw,
            extra_context=self._get_extra_context(
                stock_name, normalized_ticker, market_info
            ),
            is_etf=is_etf,
        )

        report = await self._call_llm(
            prompt,
            persona_id=self._get_persona_id(is_etf=is_etf),
        )
        logger.info(f"基本面分析师完成分析: {ticker}, 报告长度: {len(report)}")
        return report

    def _get_extra_context(
        self, stock_name: str, ticker: str, market_info: dict
    ) -> str:
        """获取额外上下文"""
        is_etf = market_info.get("is_etf", False)
        if is_etf:
            return f"""## 分析要求
请重点关注 {stock_name}（{ticker}）的ETF基本面分析要点：

1. **净值表现**：单位净值、累计净值的走势和增长率
2. **折溢价水平**：二级市场交易价格与IOPV（基金参考净值）的偏离程度
3. **跟踪效果**：基金净值与跟踪指数的偏离度和跟踪误差
4. **资金流向**：ETF份额变化、主力资金进出情况
5. **基金规模**：最新AUM（管理规模）及其变化趋势
6. **费率结构**：管理费、托管费等对长期收益的影响

## 市场特点
- 市场类型：{market_info["market_name"]}
- 货币单位：{market_info["currency_name"]}（{market_info["currency_symbol"]}）
- 投资品种：ETF（交易所交易基金）

⚠️ 注意：ETF无PE、PB、ROE等传统财务指标，请重点分析净值、折溢价、跟踪误差等基金特有指标。
"""
        return f"""## 分析要求
请重点关注 {stock_name}（{ticker}）的基本面分析要点：

1. **估值水平**：PE、PB是否处于历史低位/高位
2. **盈利能力**：ROE、毛利率、净利率是否稳定
3. **成长性**：营收和利润增长率
4. **财务健康**：资产负债率、现金流状况
5. **行业对比**：与行业平均水平的比较

## 市场特点
- 市场类型：{market_info["market_name"]}
- 货币单位：{market_info["currency_name"]}（{market_info["currency_symbol"]}）

请基于上述数据，进行专业的基本面分析。
"""
