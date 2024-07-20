from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import nacl.signing
import base64

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for simplicity; adjust as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Wallet(BaseModel):
    sol: str
    eth: str
    sig: str

def init_db():
    conn = sqlite3.connect("wallets.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        sol_address TEXT PRIMARY KEY,
        eth_address TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

@app.on_event("startup")
def startup():
    init_db()

@app.get("/get_wallet")
def get_wallet(solAddress: str):
    print(f"Fetching wallet for solAddress: {solAddress}")
    conn = sqlite3.connect("wallets.db")
    cursor = conn.cursor()
    cursor.execute("SELECT eth_address FROM users WHERE sol_address = ?", (solAddress,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return {"eth": result[0]}
    else:
        print("Wallet not found")
        raise HTTPException(status_code=404, detail="Wallet not found")

@app.post("/save_wallet")
def save_wallet(wallet: Wallet):
    print(f"Saving wallet for sol: {wallet.sol}, eth: {wallet.eth}")
    message = f"Now you certify that you want to receive tokens in the following wallet. Eth wallet: {wallet.eth}, your solana wallet: {wallet.sol}"
    encoded_message = message.encode('utf-8')
    
    try:
        signature = base64.b64decode(wallet.sig)
        verify_key = nacl.signing.VerifyKey(bytes.fromhex(wallet.sol))
        verify_key.verify(encoded_message, signature)
        print("Signature is valid")
    except Exception as e:
        print(f"Invalid signature: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    conn = sqlite3.connect("wallets.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (sol_address, eth_address) VALUES (?, ?) ON CONFLICT(sol_address) DO UPDATE SET eth_address = excluded.eth_address", (wallet.sol, wallet.eth))
    conn.commit()
    conn.close()

    print("Successfully saved")
    return {"message": "Successfully saved"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
