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

1. **净值与价格表现**：区分基金净值变化和二级市场价格波动，说明是否同步。
2. **折溢价水平**：判断二级市场价格相对IOPV/净值是否异常，给出套利或追高风险。
3. **跟踪效果**：关注跟踪指数、跟踪误差、样本区间和近期偏离原因。
4. **资金流向**：结合份额变化、成交活跃度和主力资金，判断资金是持续流入还是短期交易。
5. **基金规模与流动性**：规模过小、成交稀疏或换手异常时必须提示流动性风险。
6. **费率与持有成本**：说明管理费、托管费、交易摩擦对中长期收益的影响。
7. **适配场景**：明确该ETF更适合短线交易、波段配置、行业轮动还是长期资产配置。

## 市场特点
- 市场类型：{market_info["market_name"]}
- 货币单位：{market_info["currency_name"]}（{market_info["currency_symbol"]}）
- 投资品种：ETF（交易所交易基金）

⚠️ 注意：ETF无PE、PB、ROE等传统财务指标，请重点分析净值、折溢价、跟踪误差等基金特有指标。
"""
        return f"""## 分析要求
请重点关注 {stock_name}（{ticker}）的基本面分析要点：

1. **估值水平**：PE、PB、PS必须结合历史分位、行业对比、成长速度和盈利周期判断，不要单看绝对高低。
2. **盈利质量**：ROE、毛利率、净利率、净利润和经营现金流要互相印证；利润增长但现金流差时需降权。
3. **成长性拆解**：区分收入增长、利润率改善、费用压缩、一次性收益、并表或非经常性损益。
4. **财务健康**：关注资产负债率、短债压力、现金储备、应收账款、存货和自由现金流。
5. **行业对比**：至少指出一个相对行业更强或更弱的指标；缺少行业数据时说明无法验证。
6. **估值-业绩匹配**：判断当前估值是否已经反映增长预期，并给出估值修复或回落的触发条件。
7. **情景分析**：给出乐观、基准、悲观三种情景下最关键的驱动或风险。

## 市场特点
- 市场类型：{market_info["market_name"]}
- 货币单位：{market_info["currency_name"]}（{market_info["currency_symbol"]}）

请基于上述数据，输出可验证的基本面判断，不要把行业常识当作该公司的确定结论。
"""
