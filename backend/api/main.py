from fastapi import FastAPI

app=FastAPI()

@app.get("/")
def read_root():
    return{"message":"Tourism Decision Support System API is running."}