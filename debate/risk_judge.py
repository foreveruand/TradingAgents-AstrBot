"""
风险裁判 - 负责评估整体投资风险并给出风险等级
"""

from astrbot.api import logger

from ..personas import PERSONA_RISK_JUDGE


class RiskJudge:
    """风险裁判 - 评估整体投资风险"""

    def __init__(self, llm, data_fetcher):
        self.llm = llm
        self.data_fetcher = data_fetcher

    async def assess_risk(
        self, ticker: str, trade_date: str, context: dict, debate_report: str
    ) -> str:
        """
        评估投资风险

        Args:
            ticker: 股票代码
            trade_date: 交易日期
            context: 包含市场分析、基本面分析、新闻分析等上下文
            debate_report: 辩论综合报告

        Returns:
            风险评估报告
        """
        logger.info(f"风险裁判开始评估风险: {ticker}")

        from ..utils.stock_utils import StockUtils

        market_info = StockUtils.get_market_info(ticker)
        normalized_ticker = market_info["normalized_ticker"]
        stock_name = StockUtils.get_stock_name(ticker)

        # 获取市场数据用于风险评估
        market_data = await self.data_fetcher.get_market_data(
            normalized_ticker, trade_date
        )

        prompt = self._build_risk_prompt(
            ticker=normalized_ticker,
            stock_name=stock_name,
            trade_date=trade_date,
            market_info=market_info,
            market_data=market_data,
            context=context,
            debate_report=debate_report,
        )

        response = await self.llm.ask(prompt, persona_id=PERSONA_RISK_JUDGE)

        logger.info(f"风险裁判完成风险评估: {ticker}")

        return response

    async def assess_risk_with_data(
        self,
        ticker: str,
        trade_date: str,
        context: dict,
        debate_report: str,
        market_data_raw,
    ) -> str:
        """
        使用预获取的市场数据评估投资风险（不再重新获取数据）

        Args:
            ticker: 股票代码
            trade_date: 交易日期
            context: 包含市场分析、基本面分析、新闻分析等上下文
            debate_report: 辩论综合报告
            market_data_raw: 预获取的市场数据

        Returns:
            风险评估报告
        """
        logger.info(f"风险裁判开始评估风险（预取数据）: {ticker}")

        from ..utils.stock_utils import StockUtils

        market_info = StockUtils.get_market_info(ticker)
        normalized_ticker = market_info["normalized_ticker"]
        stock_name = StockUtils.get_stock_name(ticker)

        prompt = self._build_risk_prompt(
            ticker=normalized_ticker,
            stock_name=stock_name,
            trade_date=trade_date,
            market_info=market_info,
            market_data=market_data_raw,
            context=context,
            debate_report=debate_report,
        )

        response = await self.llm.ask(prompt, persona_id=PERSONA_RISK_JUDGE)

        logger.info(f"风险裁判完成风险评估: {ticker}")

        return response

    def _build_risk_prompt(
        self,
        ticker: str,
        stock_name: str,
        trade_date: str,
        market_info: dict,
        market_data: dict,
        context: dict,
        debate_report: str,
    ) -> str:
        """构建风险评估提示词"""

        # 提取市场数据的关键风险指标
        volatility = "未知"
        volume_ratio = "未知"

        if market_data and "data" in market_data:
            data = market_data.get("data", {})
            if "volatility" in data:
                volatility = data.get("volatility", "未知")
            if "volume_ratio" in data:
                volume_ratio = data.get("volume_ratio", "未知")

        # 判断是否为快速分析模式（无多空辩论）
        is_quick_mode = not debate_report or "快速分析模式" in debate_report

        if is_quick_mode:
            debate_section = """## 分析模式
本次为快速分析模式，未进行多空辩论。请直接基于以下市场技术面分析、基本面分析和新闻面分析进行综合风险评估。"""
        else:
            debate_section = f"""## 辩论综合报告
{debate_report}"""

        return f"""## 股票信息
- 股票名称：{stock_name}
- 股票代码：{ticker}
- 市场：{market_info["market_name"]}
- 交易日期：{trade_date}

## 市场数据摘要
- 波动率：{volatility}
- 量比：{volume_ratio}
- 市场：{market_info["market_name"]}

{debate_section}

## 已有分析背景
### 市场技术面分析
{context.get("market_analysis", "暂无市场技术面分析")}

### 基本面分析
{context.get("fundamentals_analysis", "暂无基本面分析")}

### 新闻面分析
{context.get("news_analysis", "暂无新闻面分析")}

## 你的任务
请进行全面的风险评估，并把风险结论转换成可执行的仓位与止损约束：

### ⚠️ 风险评估报告

## 🎯 风险等级
[综合评估：极高风险/高风险/中等风险/低风险/极低风险；必须说明等级来自哪些证据]

## 📊 风险因素分解

### 🔴 高风险因素
[列出最主要的1-3个高风险因素，每个都要有数据或事件依据、触发条件和可能影响]

### 🟡 中等风险因素
[列出中等风险因素，并说明为什么不是高风险]

### 🟢 低风险因素
[只列对决策有意义的低风险因素；没有就写“暂无明确低风险缓冲”]

## 💰 风险收益比
[用最近支撑/压力、波动率、量比或关键均线估算上行空间和下行空间；无法量化时说明缺失数据]

## 🛡️ 风险缓解建议
[给出仓位建议、止损/减仓位、加仓确认条件、事件跟踪项；区分短线和波段]

## ⚡ 紧急风险提示
[只有存在数据或事件支持时才写；没有则写“暂无紧急风险信号”]

## 📋 投资风险总结
[用3-5句话总结是否值得参与、适合什么风险偏好、最关键的观察点]

## 约束
- 不要输出“投资需谨慎”作为主要结论，必须给出具体风险控制动作。
- 若技术面、基本面、新闻面互相冲突，要说明以哪个维度为主、为什么。
- 若缺少关键价位或波动数据，明确标注无法计算，不要编造止损价。

"""
