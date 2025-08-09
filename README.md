# CrystalTrust Backend

CrystalTrust Backend is the **core API** powering the Crystal Bank virtual financial system.  
It handles account management, transactions, authentication, and integrations with external services like Telegram bots.

## Features

- **Account Management**  
  Create and manage user and business accounts linked to Minecraft nicknames.

- **Transactions**  
  Deposit, withdraw, and transfer funds between accounts with full validation and transaction history.

- **Security**  
  JWT-based authentication, transaction status verification, and role-based permissions.

- **Telegram Bot Integration**  
  API endpoints used by the Crystal Bank Telegram bot for secure financial operations.

- **Real-time Updates**  
  Server-Sent Events (SSE) for instant balance and transaction status updates.

## Technology Stack

- **Framework:** FastAPI (Python)
- **Database:** PostgreSQL
- **Messaging:** aiogram (Telegram Bot API)
- **Real-time:** Server-Sent Events (SSE)
- **Authentication:** JWT

## Planned Features

- API rate-limiting and IP-based security rules

---

### 📌 Project Goal
To provide a secure, scalable, and extensible backend for the Crystal Bank project, ensuring realistic and reliable financial operations inside Minecraft.
