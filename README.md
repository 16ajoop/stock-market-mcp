#  Stock Market AI Agent

An AI-powered stock market assistant built with **Azure AI Foundry, Azure Functions, Model Context Protocol (MCP), Alpha Vantage, and Azure Table Storage**.

The agent retrieves stock quotes, saves them to cloud storage, and retrieves historical records through MCP tools. GitHub Actions automates deployment to Azure Functions.

## Screenshots

  1. Azure AI Foundry Agent
     Shows the AI agent retrieving stock quotes and saving stock data.
       <img width="1920" height="1080" alt="01-foundry-agent" src="https://github.com/user-attachments/assets/4923b92f-9013-4984-b179-3996812fe9d7" />


  3. Health Check API
      Confirms that the Azure Functions application is running.
        <img width="953" height="515" alt="02-health-check png" src="https://github.com/user-attachments/assets/df6a2146-1124-4108-9c28-d2c947434074" />


  3. Stock Quote API
      Example response from the stock quote endpoint.
        <img width="955" height="542" alt="03-stock-quote png" src="https://github.com/user-attachments/assets/c3d0e08b-f269-49b1-8c47-7ab915a7d3ab" />

     
##  Features

- **Live stock quote retrieval:** Fetch stock information using the Alpha Vantage API.
- **MCP tool integration:** Allow the AI agent to call stock market functions.
- **Stock quote history:** Save retrieved quotes to Azure Table Storage.
- **Historical data retrieval:** Retrieve previously stored stock records by symbol.
- **Serverless backend:** Host Python functions on Azure Functions.
- **Automated deployment:** Deploy code to Azure using GitHub Actions.
- **Secure cloud access:** Use managed identity and Azure role-based access control for storage access.

##  Architecture

```text
                 User
                   |
                   v
          Azure AI Foundry Agent
                   |
                   v
        Model Context Protocol (MCP)
                   |
                   v
          Azure Functions (Python)
             /            \
            v              v
      Alpha Vantage    Azure Table Storage
       Stock Quotes     Stock Quote History
```

### How it works

1. The user asks the AI agent for a stock quote.
2. The agent invokes the appropriate MCP tool.
3. Azure Functions retrieves quote data from Alpha Vantage.
4. The agent can save the retrieved quote to Azure Table Storage.
5. The agent can retrieve previously stored quotes for a given stock symbol.
6. The agent summarizes the returned data for the user.

##  Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend implementation |
| Azure AI Foundry | AI agent and tool orchestration |
| Azure Functions | Serverless backend and HTTP API |
| Model Context Protocol (MCP) | Connects the agent to backend tools |
| Alpha Vantage | Stock market data provider |
| Azure Table Storage | Persistent storage for stock quote history |
| Azure Managed Identity | Identity-based access to Azure Storage |
| GitHub Actions | Automated deployment |
| Git | Version control |

##  MCP Tools

The project includes the following MCP tools:

| Tool | Purpose |
|---|---|
| `mcp_get_stock_quote` | Retrieves stock quote information |
| `save_stock_quote` | Saves a stock quote to Azure Table Storage |
| `get_stock_history` | Retrieves stored quote history for a stock symbol |

The project also exposes HTTP endpoints for health checks and stock quote retrieval.

##  API Endpoints

**Deployed Azure Functions base URL:**

```text
https://stock-market-mcp-pooja-bbdag9hwdqhwcmd2.eastus-01.azurewebsites.net
```

### 1. Health Check

```http
GET /api/health
```

Checks whether the deployed API is responding.

Example response:

```json
{
  "status": "ok",
  "message": "Stock Market API is running"
}
```

### 2. Get a Stock Quote

```http
GET /api/stock?symbol=IBM
```

Retrieves stock quote information for the requested symbol.

Example response:

```json
{
  "symbol": "IBM",
  "open": "251.9325",
  "high": "253.1800",
  "low": "249.1250",
  "price": "250.2500",
  "volume": "3658471",
  "latest_trading_day": "2026-10-27",
  "change": "-3.1900",
  "change_percent": "-1.2587%"
}
```

*Note: Stock prices and the example response are illustrative of a successful test performed on October 28, 2026. Market data changes over time.*

##  Stock Quote History

The application uses Azure Table Storage to persist stock quote records.

Each saved record can include:

- Stock symbol
- Trading day
- Price
- Open, high, and low prices
- Trading volume
- Price change
- Percentage change
- Timestamp when the record was stored

The `StockQuotes` table stores the quote history. The Function App uses managed identity to access Azure Storage, with the required permissions configured through Azure RBAC.

##  Local Setup

### Prerequisites

Install or configure:

- Python 3.12
- Node.js and npm (for local Azurite installation)
- Azure Functions Core Tools v4
- An Alpha Vantage API key
- An Azure Storage account, or Azurite for local storage development

### 1. Clone the repository

```powershell
git clone https://github.com/16ajoop/stock-market-mcp.git
cd stock-market-mcp
```

### 2. Create a virtual environment

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure local settings

Create a `local.settings.json` file in the project root. Use your own credentials and configuration values.

Example structure:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "ALPHA_VANTAGE_API_KEY": "YOUR_ALPHA_VANTAGE_API_KEY",
    "STORAGE_ACCOUNT_NAME": "YOUR_STORAGE_ACCOUNT_NAME"
  }
}
```

For local development with Azurite, start Azurite in a separate terminal. If you want to use Azure Table Storage directly, configure the appropriate Azure identity and permissions instead.

**Security:** Never commit `local.settings.json`, API keys, passwords, or access tokens to GitHub.

### 5. Start the application

```powershell
func start
```

Test the health endpoint locally:

```powershell
Invoke-RestMethod "http://localhost:7071/api/health"
```

Test stock quote retrieval locally:

```powershell
Invoke-RestMethod "http://localhost:7071/api/stock?symbol=IBM"
```

##  Azure Deployment

The project uses GitHub Actions to automate deployment to Azure Functions.

The workflow is located at:

```text
.github/workflows/main_stock-market-mcp-pooja.yml
```

The deployment workflow:

1. Checks out the repository.
2. Sets up Python.
3. Packages the application.
4. Authenticates to Azure using GitHub Actions and OpenID Connect.
5. Deploys the application to Azure Functions.

The deployment workflow requests remote build for the Flex Consumption hosting plan.

Required application configuration, including the Alpha Vantage API key and storage account name, must be configured securely in Azure.

##  Tested Functionality

The following functionality has been tested against the deployed application:

- [x] Azure health endpoint returns a successful response.
- [x] Stock quote endpoint retrieves IBM quote data.
- [x] Foundry agent invokes the stock quote MCP tool.
- [x] The agent saves an IBM quote using `save_stock_quote`.
- [x] The agent retrieves the saved IBM record using `get_stock_history`.
- [x] The agent retrieves an MSFT quote.
- [x] The agent saves and retrieves the MSFT record successfully.
- [x] Expected stock fields are returned by the storage tools.

These tests confirm the main quote retrieval and history workflows. They do not constitute a full load, security, or production-reliability assessment.

##  Security Considerations

- Keep API keys out of source code and version control.
- Use Azure application settings or an appropriate secret store for sensitive configuration.
- Use managed identity and least-privilege Azure RBAC permissions for storage access.
- Restrict access to protected function endpoints and MCP tools as appropriate.
- Avoid exposing function keys, connection strings, or other credentials in logs and screenshots.

##  Future Improvements

Potential extensions include:

- Price history visualizations and trend charts
- Watchlists for multiple stock symbols
- Scheduled quote collection
- Price alerts and threshold notifications
- Unit and integration tests
- Improved error handling and API rate-limit management
- Monitoring and structured logging
- A dashboard for viewing stored stock data

##  Learning Outcomes

This project provided hands-on experience with:

- Building and deploying Python-based serverless applications
- Integrating an external REST API
- Connecting an AI agent to tools using MCP
- Persisting application data in Azure Table Storage
- Configuring managed identity and Azure RBAC
- Automating cloud deployment with GitHub Actions
- Testing an AI agent's end-to-end tool workflow

## Author

**Pooja V**
[GitHub](https://github.com/16ajoop)
