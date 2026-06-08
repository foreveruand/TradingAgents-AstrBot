"""
研究主管 - 负责协调多方和空方研究，生成综合辩论报告
"""

import asyncio

from astrbot.api import logger

from ..personas import PERSONA_RESEARCH_MANAGER


class ResearchManager:
    """研究主管 - 管理辩论研究流程"""

    def __init__(self, llm, data_fetcher, bull_researcher, bear_researcher):
        self.llm = llm
        self.data_fetcher = data_fetcher
        self.bull_researcher = bull_researcher
        self.bear_researcher = bear_researcher

    async def conduct_debate(self, ticker: str, trade_date: str, context: dict) -> str:
        """
        执行多空辩论

        Args:
            ticker: 股票代码
            trade_date: 交易日期
            context: 包含市场分析、基本面分析、新闻分析等上下文

        Returns:
            辩论综合报告
        """
        logger.info(f"研究主管开始协调辩论: {ticker}")

        # 并行执行多方和空方研究（带超时保护）
        bull_task = self.bull_researcher.research(ticker, trade_date, context)
        bear_task = self.bear_researcher.research(ticker, trade_date, context)

        try:
            bull_report, bear_report = await asyncio.wait_for(
                self._run_parallel(bull_task, bear_task), timeout=180
            )
        except asyncio.TimeoutError:
            logger.error("多空辩论并行研究超时（180s）")
            return "⚠️ 多空辩论并行研究超时，请稍后重试。"

        # 处理并行执行中的异常
        if isinstance(bull_report, Exception):
            logger.error(f"多方研究异常: {bull_report}")
            bull_report = f"多方研究失败: {type(bull_report).__name__}: {bull_report}"
        if isinstance(bear_report, Exception):
            logger.error(f"空方研究异常: {bear_report}")
            bear_report = f"空方研究失败: {type(bear_report).__name__}: {bear_report}"

        # 生成综合辩论报告
        debate_report = await self._synthesize_debate(
            ticker, trade_date, context, bull_report, bear_report
        )

        logger.info(f"研究主管完成辩论协调: {ticker}")

        return debate_report

    # REVIEW-NOTE: 保留 _run_parallel 封装，因 conduct_debate 中已用 asyncio.wait_for 超时包裹，内联会使超时逻辑与 gather 混杂
    async def _run_parallel(self, *tasks):
        """并行运行多个任务"""
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

    async def _synthesize_debate(
        self,
        ticker: str,
        trade_date: str,
        context: dict,
        bull_report: str,
        bear_report: str,
    ) -> str:
        """综合多方和空方观点，生成辩论报告"""

        from ..utils.stock_utils import StockUtils

        market_info = StockUtils.get_market_info(ticker)
        stock_name = StockUtils.get_stock_name(ticker)

        prompt = f"""## 股票信息
- 股票名称：{stock_name}
- 股票代码：{ticker}
- 市场：{market_info["market_name"]}
- 交易日期：{trade_date}

## 多方研究报告
{bull_report}

## 空方研究报告
{bear_report}

## 已有分析背景
### 市场技术面分析
{context.get("market_analysis", "暂无市场技术面分析")}

### 基本面分析
{context.get("fundamentals_analysis", "暂无基本面分析")}

### 新闻面分析
{context.get("news_analysis", "暂无新闻面分析")}

## 你的任务
请综合多空双方的观点，生成一份客观、压缩、可执行的辩论综合报告：

### 🎯 辩论综合报告

## 📊 多空力量对比
[用表格对比多方/空方最强3条证据、证据类型、强度、是否被对方有效反驳]

## ⚖️ 双方共识
[多空双方都认可的事实或数据，不要写价值判断]

## 🔥 核心分歧
[列出最关键的1-3个分歧，并说明哪个数据或事件能验证]

## 📈 多方核心逻辑
[只保留最重要的多方链条：触发条件 → 价格/估值/业绩影响 → 失效条件]

## 📉 空方核心逻辑
[只保留最重要的空方链条：触发条件 → 下行风险 → 失效条件]

## 🎯 综合评估
[给出多空胜率倾向：偏多/中性偏多/中性/中性偏空/偏空，并说明权重排序]

## 💡 投资建议
[给出适合的操作层级：观察、轻仓试探、持有、减仓、回避；同时写明确认位、失效位和主要跟踪事项]

---
重要提醒：
- 必须使用上述格式输出
- 客观平衡地呈现多空双方观点
- 明确指出双方共识和分歧
- 给出基于辩论的综合投资建议
- 不要重复粘贴多空报告原文，要提炼取舍
- 如果证据不足以支持明确方向，结论应为中性并说明还缺什么数据
"""

        try:
            response = await asyncio.wait_for(
                self.llm.ask(prompt, persona_id=PERSONA_RESEARCH_MANAGER),
                timeout=120,
            )
        except asyncio.TimeoutError:
            logger.error("辩论综合报告生成超时（120s）")
            response = "⚠️ 辩论综合报告生成超时，请稍后重试。"

        return response
