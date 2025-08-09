from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.endpoints.business import create
from api.endpoints.me import transfer, recipients, transactions, summary, accounts, profile
from api.logging_middleware import RequestLoggerMiddleware

app = FastAPI(title="CrystalBank API")

app.add_middleware(RequestLoggerMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://tonalyze.ru"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profile.router)
app.include_router(accounts.router)
app.include_router(summary.router)
app.include_router(transactions.router)
app.include_router(recipients.router)
app.include_router(transfer.router)
app.include_router(create.router)

