
import os
import requests

from fastapi import FastAPI, HTTPException

app = FastAPI(
    title="Zoo Visitors API",
    description="API สถิติผู้เข้าชมสวนสัตว์ ปีงบประมาณ 2569",
    version="1.0.0"
)

# Resource ID ของชุดข้อมูลสวนสัตว์
RESOURCE_ID = "57a5cad9-d533-4bd1-b3a5-e310bc13eeaa"

# Open Data API Endpoint
DATA_URL = "https://opend.data.go.th/get-ckan/datastore_search"


@app.get("/")
def home():
    return {
        "message": "Zoo Visitors API is running",
        "docs": "/docs"
    }


@app.get("/api/zoo-visitors")
def get_zoo_visitors():

    # อ่าน API KEY จาก Render Environment
    api_key = os.getenv("OPEND_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OPEND_API_KEY is not configured"
        )

    # กำหนด Parameters
    params = {
        "resource_id": RESOURCE_ID,
        "limit": 5
    }

    # กำหนด Headers
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

        # ตรวจสอบ HTTP Status
        if response.status_code in (401, 403):
            raise HTTPException(
                status_code=502,
                detail={
                    "message": "Open Data API rejected the request",
                    "upstream_status": response.status_code,
                    "solution": "ตรวจสอบ API KEY และสิทธิ์การเข้าถึง API"
                }
            )

        response.raise_for_status()

        # แปลงข้อมูล JSON
        result = response.json()

        if not result.get("success"):
            raise HTTPException(
                status_code=502,
                detail="Data.go.th API returned an error"
            )

        data_result = result.get("result", {})
        records = data_result.get("records", [])

        if not records:
            raise HTTPException(
                status_code=404,
                detail="ไม่พบข้อมูลใน Resource ID ที่กำหนด"
            )

        # ส่งข้อมูลกลับ
        return {
            "status": "success",
            "message": "ดึงข้อมูลสำเร็จ",
            "dataset": "zoo-visitors2569",
            "organization": "องค์การสวนสัตว์แห่งประเทศไทย ในพระบรมราชูปถัมภ์",
            "fiscal_year": 2569,
            "resource_id": RESOURCE_ID,
            "source": "https://data.go.th/dataset/zoo-visitors2569",
            "total_records": data_result.get("total", len(records)),
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
            detail="Invalid JSON response from Open Data API"
        )
