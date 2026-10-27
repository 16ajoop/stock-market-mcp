import json
import os
import urllib.parse
import urllib.request
import urllib.error

import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps({"status": "ok", "message": "Stock Market API is running"}),
        mimetype="application/json",
        status_code=200,
    )


@app.route(route="stock", methods=["GET"])
def get_stock_quote(req: func.HttpRequest) -> func.HttpResponse:
    symbol = (req.params.get("symbol") or "").strip().upper()
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")

    if not symbol:
        return func.HttpResponse(
            json.dumps({"error": "Provide a stock symbol, e.g. ?symbol=IBM"}),
            mimetype="application/json",
            status_code=400,
        )

    if not api_key:
        return func.HttpResponse(
            json.dumps({"error": "ALPHA_VANTAGE_API_KEY is not configured"}),
            mimetype="application/json",
            status_code=500,
        )

    params = urllib.parse.urlencode({
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "apikey": api_key,
    })
    url = f"https://www.alphavantage.co/query?{params}"

    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))

        quote = data.get("Global Quote", {})
        if not quote:
            return func.HttpResponse(
                json.dumps({
                    "error": "No quote returned. Check the symbol, API response, or API rate limit.",
                    "details": data,
                }),
                mimetype="application/json",
                status_code=502,
            )

        result = {
            "symbol": quote.get("01. symbol"),
            "open": quote.get("02. open"),
            "high": quote.get("03. high"),
            "low": quote.get("04. low"),
            "price": quote.get("05. price"),
            "volume": quote.get("06. volume"),
            "latest_trading_day": quote.get("07. latest trading day"),
            "change": quote.get("09. change"),
            "change_percent": quote.get("10. change percent"),
        }
        return func.HttpResponse(
            json.dumps(result),
            mimetype="application/json",
            status_code=200,
        )

    except Exception:
        return func.HttpResponse(
            json.dumps({"error": "Unable to retrieve the stock quote. Check the API key and network connection."}),
            mimetype="application/json",
            status_code=502,
        )


# MCP tool: allows an AI agent to retrieve a stock quote.
STOCK_SYMBOL_PROPERTY = json.dumps([
    {
        "propertyName": "symbol",
        "propertyType": "string",
        "description": "Stock ticker symbol, for example IBM or MSFT.",
        "isRequired": True
    }
])


@app.mcp_tool_trigger(
    arg_name="context",
    tool_name="get_stock_quote",
    description="Retrieve the latest available stock quote for a ticker symbol.",
    tool_properties=STOCK_SYMBOL_PROPERTY,
)
def mcp_get_stock_quote(context: str) -> str:
    """Return stock quote data to an MCP client."""
    try:
        invocation = json.loads(context)
        arguments = invocation.get("arguments", {})
        symbol = (arguments.get("symbol") or "").strip().upper()

        if not symbol:
            return json.dumps({"error": "Provide a stock symbol, such as IBM."})

        api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if not api_key:
            return json.dumps({"error": "Stock quote API key is not configured."})

        params = urllib.parse.urlencode({
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": api_key,
        })
        url = f"https://www.alphavantage.co/query?{params}"

        with urllib.request.urlopen(url, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))

        quote = data.get("Global Quote", {})
        if not quote:
            return json.dumps({
                "error": "No quote returned.",
                "details": data
            })

        result = {
            "symbol": quote.get("01. symbol"),
            "open": quote.get("02. open"),
            "high": quote.get("03. high"),
            "low": quote.get("04. low"),
            "price": quote.get("05. price"),
            "volume": quote.get("06. volume"),
            "latest_trading_day": quote.get("07. latest trading day"),
            "change": quote.get("09. change"),
            "change_percent": quote.get("10. change percent"),
        }
        return json.dumps(result)

    except Exception:
        return json.dumps({
            "error": "Unable to retrieve the stock quote."
        })