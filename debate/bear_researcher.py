"""
空方研究员 - 负责挖掘股票的利空因素
"""

from astrbot.api import logger

from ..personas import PERSONA_BEAR_RESEARCHER


class BearResearcher:
    """空方研究员 - 寻找导致股价下跌的风险因素"""

    def __init__(self, llm, data_fetcher):
        self.llm = llm
        self.data_fetcher = data_fetcher

    async def research(self, ticker: str, trade_date: str, context: dict) -> str:
        """
        研究利空因素

        Args:
            ticker: 股票代码
            trade_date: 交易日期
            context: 包含市场分析、基本面分析等上下文

        Returns:
            空方研究报告
        """
        logger.info(f"空方研究员开始研究: {ticker}")

        from ..utils.stock_utils import StockUtils

        market_info = StockUtils.get_market_info(ticker)
        normalized_ticker = market_info["normalized_ticker"]
        stock_name = StockUtils.get_stock_name(ticker)

        prompt = self._build_bear_prompt(
            ticker=normalized_ticker,
            stock_name=stock_name,
            trade_date=trade_date,
            market_info=market_info,
            context=context,
        )

        response = await self.llm.ask(prompt, persona_id=PERSONA_BEAR_RESEARCHER)

        logger.info(f"空方研究员完成研究: {ticker}")

        return response

    def _build_bear_prompt(
        self,
        ticker: str,
        stock_name: str,
        trade_date: str,
        market_info: dict,
        context: dict,
    ) -> str:
        """构建空方研究提示词"""

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
请从以下角度深入挖掘该股票的利空因素：

### 📉 利空因素分析

#### 1. 空头核心证据
- 从技术、基本面、估值、消息、资金、宏观或行业中挑选最强的3-5条证据，按影响程度排序。
- 每条证据必须引用已有分析中的具体数据或结论，不要重复空泛判断。

#### 2. 估值回落风险
- 当前估值是否高于历史分位或行业可比水平？
- 若增长不达预期，估值回落可能由什么触发？

#### 3. 业绩与财务风险
- 是否存在利润率下滑、现金流弱、负债压力、应收/存货异常或增长放缓？
- 哪些指标最能证明风险正在扩大？

#### 4. 技术面压力
- 是否出现跌破支撑、均线空头、放量下跌、动量背离或反弹无量？
- 哪个价位或指标被收复后，空头逻辑需要降级？

#### 5. 消息与预期差
- 利空新闻是否改变基本面，还是仅是短期情绪？
- 市场是否已经充分反映该风险，仍需跟踪什么验证点？

#### 6. 反方观点回应
- 多方最可能引用什么利好？
- 空头观点被证伪的最关键条件是什么？

#### 7. 仓位风险
- 什么情况下应减仓、回避或只保留观察仓？
- 若风险尚未确认，应说明为什么不能给强空结论。

## 输出要求
1. 客观分析利空因素，但不要过度悲观
2. 引用具体数据支持你的观点
3. 区分短期和长期因素
4. 给出股价可能下跌的核心逻辑、触发条件、失效条件和风险等级
5. 删除缺乏证据的利空点，不要为了凑满角度而泛泛而谈
"""
