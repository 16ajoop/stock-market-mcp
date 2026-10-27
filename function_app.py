import json
import os
import urllib.parse
import urllib.request
import urllib.error

import azure.functions as func

from datetime import datetime, timezone
from azure.data.tables import TableServiceClient
from azure.identity import DefaultAzureCredential

def get_stock_table():
    account_name = os.getenv("STORAGE_ACCOUNT_NAME")

    if not account_name:
        raise ValueError("STORAGE_ACCOUNT_NAME is not configured")

    endpoint = f"https://{account_name}.table.core.windows.net"

    credential = DefaultAzureCredential()
    service = TableServiceClient(
        endpoint=endpoint,
        credential=credential,
    )

    return service.get_table_client(table_name="StockQuotes")

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


# Properties for saving a stock quote.
SAVE_QUOTE_PROPERTIES = json.dumps([
    {
        "propertyName": "symbol",
        "propertyType": "string",
        "description": "Stock ticker symbol, for example IBM.",
        "isRequired": True
    },
    {
        "propertyName": "price",
        "propertyType": "string",
        "description": "Latest available stock price.",
        "isRequired": True
    },
    {
        "propertyName": "open",
        "propertyType": "string",
        "description": "Opening price.",
        "isRequired": True
    },
    {
        "propertyName": "high",
        "propertyType": "string",
        "description": "Daily high.",
        "isRequired": True
    },
    {
        "propertyName": "low",
        "propertyType": "string",
        "description": "Daily low.",
        "isRequired": True
    },
    {
        "propertyName": "volume",
        "propertyType": "string",
        "description": "Trading volume.",
        "isRequired": True
    },
    {
        "propertyName": "trading_day",
        "propertyType": "string",
        "description": "Trading day in YYYY-MM-DD format.",
        "isRequired": True
    },
    {
        "propertyName": "change",
        "propertyType": "string",
        "description": "Absolute price change.",
        "isRequired": True
    },
    {
        "propertyName": "change_percent",
        "propertyType": "string",
        "description": "Percentage price change.",
        "isRequired": True
    }
])

GET_HISTORY_PROPERTIES = json.dumps([
    {
        "propertyName": "symbol",
        "propertyType": "string",
        "description": "Stock ticker symbol, for example IBM.",
        "isRequired": True
    }
])


@app.mcp_tool_trigger(
    arg_name="context",
    tool_name="save_stock_quote",
    description="Save a retrieved stock quote to Azure Table Storage.",
    tool_properties=SAVE_QUOTE_PROPERTIES,
)
def save_stock_quote(context: str) -> str:
    try:
        invocation = json.loads(context)
        args = invocation.get("arguments", {})

        symbol = (args.get("symbol") or "").strip().upper()
        trading_day = (args.get("trading_day") or "").strip()

        if not symbol or not trading_day:
            return json.dumps({
                "success": False,
                "error": "Symbol and trading_day are required."
            })

        # Validate date format before writing to storage.
        datetime.strptime(trading_day, "%Y-%m-%d")

        table = get_stock_table()

        # Use a unique row key so multiple quotes for the same
        # symbol and trading day can be stored.
        entity = {
            "PartitionKey": symbol,
            "RowKey": datetime.now(timezone.utc).strftime(
                "%Y%m%dT%H%M%S%fZ"
            ),
            "Symbol": symbol,
            "Price": args["price"],
            "Open": args["open"],
            "High": args["high"],
            "Low": args["low"],
            "Volume": args["volume"],
            "TradingDay": trading_day,
            "Change": args["change"],
            "ChangePercent": args["change_percent"],
            "StoredAt": datetime.now(timezone.utc).isoformat()
        }

        table.create_entity(entity=entity)

        return json.dumps({
            "success": True,
            "message": "Stock quote saved successfully.",
            "symbol": symbol,
            "trading_day": trading_day,
            "price": args["price"]
        })

    except Exception:
        return json.dumps({
            "success": False,
            "error": (
                "Unable to save the stock quote. "
                "Check the storage configuration and permissions."
            )
        })


@app.mcp_tool_trigger(
    arg_name="context",
    tool_name="get_stock_history",
    description="Retrieve previously saved stock quotes for a symbol.",
    tool_properties=GET_HISTORY_PROPERTIES,
)
def get_stock_history(context: str) -> str:
    try:
        invocation = json.loads(context)
        args = invocation.get("arguments", {})
        symbol = (args.get("symbol") or "").strip().upper()

        if not symbol:
            return json.dumps({
                "error": "Provide a stock symbol, such as IBM."
            })

        table = get_stock_table()

        entities = table.query_entities(
            query_filter=f"PartitionKey eq '{symbol}'"
        )

        records = []
        for entity in entities:
            records.append({
                "symbol": entity.get("Symbol"),
                "price": entity.get("Price"),
                "open": entity.get("Open"),
                "high": entity.get("High"),
                "low": entity.get("Low"),
                "volume": entity.get("Volume"),
                "trading_day": entity.get("TradingDay"),
                "change": entity.get("Change"),
                "change_percent": entity.get("ChangePercent"),
                "stored_at": entity.get("StoredAt")
            })

        records.sort(
            key=lambda item: item.get("stored_at") or "",
            reverse=True
        )

        return json.dumps({
            "symbol": symbol,
            "count": len(records),
            "quotes": records
        })

    except Exception:
        return json.dumps({
            "error": (
                "Unable to retrieve stock history. "
                "Check the storage configuration and permissions."
            )
        })