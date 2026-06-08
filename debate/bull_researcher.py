"""
多方研究员 - 负责挖掘股票的利好因素
"""

from astrbot.api import logger

from ..personas import PERSONA_BULL_RESEARCHER


class BullResearcher:
    """多方研究员 - 寻找支撑股价上涨的证据"""

    def __init__(self, llm, data_fetcher):
        self.llm = llm
        self.data_fetcher = data_fetcher

    async def research(self, ticker: str, trade_date: str, context: dict) -> str:
        """
        研究利好因素

        Args:
            ticker: 股票代码
            trade_date: 交易日期
            context: 包含市场分析、基本面分析等上下文

        Returns:
            多方研究报告
        """
        logger.info(f"多方研究员开始研究: {ticker}")

        from ..utils.stock_utils import StockUtils

        market_info = StockUtils.get_market_info(ticker)
        normalized_ticker = market_info["normalized_ticker"]
        stock_name = StockUtils.get_stock_name(ticker)

        prompt = self._build_bull_prompt(
            ticker=normalized_ticker,
            stock_name=stock_name,
            trade_date=trade_date,
            market_info=market_info,
            context=context,
        )

        response = await self.llm.ask(prompt, persona_id=PERSONA_BULL_RESEARCHER)

        logger.info(f"多方研究员完成研究: {ticker}")

        return response

    def _build_bull_prompt(
        self,
        ticker: str,
        stock_name: str,
        trade_date: str,
        market_info: dict,
        context: dict,
    ) -> str:
        """构建多方研究提示词"""

        return f"""## 股票信息
- 股票名称：{stock_name}
- 股票代码：{ticker}
- 市场：{market_info["market_name"]}
- 交易日期：{trade_date}

## 已有分析信息
以下是其他分析师提供的信息：

### 市场技术面分析
{context.get("market_analysis", "暂无市场技术面分析")}

### 基本面分析
{context.get("fundamentals_analysis", "暂无基本面分析")}

### 新闻面分析
{context.get("news_analysis", "暂无新闻面分析")}

## 你的任务
请从以下角度深入挖掘该股票的利好因素：

### 📈 利好因素分析

#### 1. 多头核心证据
- 从技术、基本面、估值、消息、资金中挑选最强的3-5条证据，按影响程度排序。
- 每条证据必须引用已有分析中的具体数据或结论，不要重复空泛判断。

#### 2. 估值修复潜力
- 当前估值是否低于历史分位或行业可比水平？
- 估值修复需要什么触发条件，例如业绩兑现、政策催化、资金回流或技术突破？

#### 3. 业绩增长驱动
- 增长来自主营改善、利润率提升、周期反转还是一次性因素？
- 哪些数据能证明增长具备持续性？

#### 4. 技术面机会
- 是否出现趋势、量能、动量共振？
- 买入或加仓的确认位是什么，跌破哪里说明多头逻辑失效？

#### 5. 催化与预期差
- 近期新闻或政策是否带来尚未充分反映的预期差？
- 后续应跟踪什么事件或指标验证？

#### 6. 反方观点回应
- 空方最可能质疑什么？
- 多头观点被证伪的最关键条件是什么？

## 输出要求
1. 客观分析利好因素，但不要过度乐观
2. 引用具体数据支持你的观点
3. 区分短期和长期因素
4. 给出支撑股价上涨的核心逻辑、触发条件、失效条件和适合仓位
5. 删除缺乏证据的利好点，不要为了凑满角度而泛泛而谈
"""
