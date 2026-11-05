
import os
import requests

from fastapi import FastAPI, HTTPException

app = FastAPI(
    title="Zoo Visitors API",
    description="API สถิติผู้เข้าชมสวนสัตว์ ปีงบประมาณ 2569",
    version="1.0.1"
)

RESOURCE_ID = "57a5cad9-d533-4bd1-b3a5-e310bc13eeaa"

DATA_URL = "https://opend.data.go.th/get-ckan/datastore_search"


@app.get("/")
def home():
    return {
        "message": "Zoo Visitors API is running",
        "docs": "/docs"
    }


@app.get("/api/zoo-visitors")
def get_zoo_visitors():

    # อ่าน API KEY จาก Render
    api_key = os.getenv("OPEND_API_KEY", "").strip()

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="ไม่พบ OPEND_API_KEY ใน Render Environment"
        )

    params = {
        "resource_id": RESOURCE_ID,
        "limit": 5
    }

    # ตามคู่มือ Data.go.th หน้า 36-37
    headers = {
        "api-key": api_key,
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(
            DATA_URL,
            params=params,
            headers=headers,
            timeout=30
        )

        # ตรวจสอบสถานะจาก Data.go.th
        if response.status_code == 403:
            raise HTTPException(
                status_code=502,
                detail={
                    "message": "Open Data API rejected the request",
                    "upstream_status": 403,
                    "solution": "ตรวจสอบ API KEY และสิทธิ์การเข้าถึง API"
                }
            )

        response.raise_for_status()

        result = response.json()

        if not result.get("success"):
            raise HTTPException(
                status_code=502,
                detail={
                    "message": "Data.go.th API returned an error",
                    "response": result
                }
            )

        records = result.get("result", {}).get("records", [])

        return {
            "status": "success",
            "dataset": "zoo-visitors2569",
            "organization": "องค์การสวนสัตว์แห่งประเทศไทย",
            "fiscal_year": 2569,
            "resource_id": RESOURCE_ID,
            "source": "https://data.go.th/dataset/zoo-visitors2569",
            "total_records": result["result"].get(
                "total", len(records)
            ),
            "returned_records": len(records),
            "data": records
        }

    except HTTPException:
        raise

    except requests.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Data.go.th connection error: {str(e)}"
        )

    except ValueError:
        raise HTTPException(
            status_code=502,
            detail="Data.go.th returned invalid JSON"
        )
