
from fastapi import FastAPI, HTTPException
import requests

app = FastAPI(
    title="Zoo Visitors API",
    description="API สถิติผู้เข้าชมสวนสัตว์ ปีงบประมาณ 2569",
    version="1.0.0"
)

RESOURCE_ID = "57a5cad9-d533-4bd1-b3a5-e310bc13eeaa"
DATA_URL = "https://data.go.th/api/3/action/datastore_search"


@app.get("/")
def home():
    return {
        "message": "Zoo Visitors API is running",
        "docs": "/docs"
    }


@app.get("/api/zoo-visitors")
def get_zoo_visitors():

    params = {
        "resource_id": RESOURCE_ID,
        "limit": 5
    }

    try:
        response = requests.get(
            DATA_URL,
            params=params,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json",
                "Referer": "https://data.go.th/"
            },
            timeout=30
        )

    except requests.Timeout:
        raise HTTPException(
            status_code=504,
            detail="Data.go.th connection timeout"
        )

    except requests.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Connection error: {str(e)}"
        )

    # ตรวจสอบ HTTP Status จาก Data.go.th
    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Data.go.th rejected the request",
                "upstream_status": response.status_code,
                "upstream_response": response.text[:1000]
            }
        )

    # ตรวจสอบ JSON
    try:
        result = response.json()
    except ValueError:
        raise HTTPException(
            status_code=502,
            detail="Data.go.th returned invalid JSON"
        )

    if not result.get("success"):
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Data.go.th API returned an error",
                "response": result
            }
        )

    dataset = result.get("result", {})
    records = dataset.get("records", [])

    if not records:
        raise HTTPException(
            status_code=404,
            detail="ไม่พบข้อมูลใน Resource ID ที่กำหนด"
        )

    return {
        "status": "success",
        "dataset": "zoo-visitors2569",
        "organization": "องค์การสวนสัตว์แห่งประเทศไทย ในพระบรมราชูปถัมภ์",
        "fiscal_year": 2569,
        "resource_id": RESOURCE_ID,
        "source": "https://data.go.th/dataset/zoo-visitors2569",
        "total_records": dataset.get("total", len(records)),
        "returned_records": len(records),
        "data": records
    }
