"""分析师基类。"""

from abc import ABC, abstractmethod

from ..utils.stock_utils import StockUtils


class BaseAnalyst(ABC):
    """分析师基类"""

    def __init__(self, llm, data_fetcher):
        """
        初始化分析师

        Args:
            llm: LLM实例，需支持 async __call__
            data_fetcher: DataFetcher实例
        """
        self.llm = llm
        self.data_fetcher = data_fetcher

    @abstractmethod
    async def analyze(self, ticker: str, trade_date: str) -> str:
        """
        执行分析并返回报告

        Args:
            ticker: 股票代码
            trade_date: 交易日期 YYYY-MM-DD

        Returns:
            分析报告文本
        """
        pass

    def _resolve_ticker_info(self, ticker: str) -> tuple[dict, str, str]:
        """统一获取市场信息、标准化代码和股票名称。

        所有子类的 analyze / analyze_with_data 方法都需要这三项，
        抽取到基类避免每个子类重复调用。

        Returns:
            (market_info, normalized_ticker, stock_name)
        """
        market_info = StockUtils.get_market_info(ticker)
        normalized_ticker = market_info["normalized_ticker"]
        stock_name = StockUtils.get_stock_name(ticker)
        return market_info, normalized_ticker, stock_name

    async def _call_llm(self, prompt: str, *, persona_id: str) -> str:
        """调用LLM生成回复，异常向上传播由调用方处理。"""
        result = await self.llm(prompt, persona_id=persona_id)
        return result

    @staticmethod
    def _build_quality_requirements() -> str:
        """返回所有分析师通用的报告质量约束。"""
        return """## 报告质量要求
- 先给可执行结论，再列关键证据；不要先铺陈大量背景。
- 每个结论必须引用上方数据中的具体指标、数值、日期、区间或新闻事件；没有数据时写“数据不足”，不要猜测。
- 明确区分短线（1-5个交易日）、波段（2-8周）和中长期（1个季度以上）的判断。
- 至少给出一个确认条件和一个失效条件，例如突破/跌破价位、均线、量能、业绩指标或事件进展。
- 如果多项指标冲突，必须说明冲突点和最终采用的权重，而不是只选择支持结论的指标。
- 输出应压缩重复解释，避免“建议关注后续变化”等没有具体观察点的空话。
"""

    @abstractmethod
    def _get_persona_id(self, *, is_etf: bool = False) -> str:
        """获取当前分析场景对应的人格 ID。"""
        raise NotImplementedError

    def _build_analysis_prompt(
        self,
        ticker: str,
        trade_date: str,
        market_info: dict,
        market_data: str = "",
        fundamentals_data: str = "",
        news_data: str = "",
        sentiment_data: str = "",
        extra_context: str = "",
        is_etf: bool = False,
    ) -> str:
        """
        构建分析提示词 - 子类可重写

        Args:
            ticker: 股票代码
            trade_date: 交易日期
            market_info: 市场信息
            market_data: 市场数据
            fundamentals_data: 基本面数据
            news_data: 新闻数据
            sentiment_data: 情绪数据
            extra_context: 额外上下文
            is_etf: 是否为ETF
        """
        from ..utils.stock_utils import StockUtils

        stock_name = StockUtils.get_stock_name(ticker)
        market_name = market_info.get("market_name", "未知")
        currency = market_info.get("currency_name", "未知")
        currency_symbol = market_info.get("currency_symbol", "")

        prompt = f"""## 分析对象
- {"基金" if is_etf else "股票"}名称: {stock_name}
- {"基金" if is_etf else "股票"}代码: {ticker}
- 所属市场: {market_name}
- 分析日期: {trade_date}
- 计价货币: {currency}（{currency_symbol}）

{extra_context}

"""

        if market_data:
            prompt += f"## 市场数据\n{market_data}\n\n"

        if fundamentals_data:
            prompt += f"## 基本面数据\n{fundamentals_data}\n\n"

        if news_data:
            prompt += f"## 新闻数据\n{news_data}\n\n"

        if sentiment_data:
            prompt += f"## 情绪数据\n{sentiment_data}\n\n"

        prompt += self._build_quality_requirements()

        return prompt
