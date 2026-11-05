
import os
import requests

from fastapi import FastAPI, HTTPException

app = FastAPI(
    title="Zoo Visitors API",
    description="API สถิติผู้เข้าชมสวนสัตว์ ปีงบประมาณ 2569",
    version="1.0.2"
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
    api_key = os.getenv("OPEND_API_KEY", "").strip()

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OPEND_API_KEY is not configured in Render"
        )

    # กำหนดพารามิเตอร์
    params = {
        "resource_id": RESOURCE_ID,
        "limit": 5
    }

    # ส่ง API KEY ผ่าน HTTP Header
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

        # ตรวจสอบสิทธิ์การเข้าถึง
        if response.status_code in (401, 403):
            raise HTTPException(
                status_code=502,
                detail={
                    "message": "Open Data API rejected the request",
                    "upstream_status": response.status_code,
                    "api_key_loaded": True,
                    "upstream_error": response.text[:2000],
                    "solution": "ตรวจสอบ API KEY และสิทธิ์การเข้าถึง API"
                }
            )

        # ตรวจสอบ HTTP Status อื่น ๆ
        response.raise_for_status()

        # แปลงข้อมูล JSON
        try:
            result = response.json()
        except ValueError:
            raise HTTPException(
                status_code=502,
                detail={
                    "message": "Data.go.th returned invalid JSON",
                    "upstream_response": response.text[:2000]
                }
            )

        # ตรวจสอบผลการเรียก API
        if not result.get("success"):
            raise HTTPException(
                status_code=502,
                detail={
                    "message": "Data.go.th API returned an error",
                    "response": result
                }
            )

        # ดึงข้อมูล Records
        api_result = result.get("result", {})
        records = api_result.get("records", [])

        # ส่งข้อมูลกลับ
        return {
            "status": "success",
            "dataset": "zoo-visitors2569",
            "organization": "องค์การสวนสัตว์แห่งประเทศไทย ในพระบรมราชูปถัมภ์",
            "fiscal_year": 2569,
            "resource_id": RESOURCE_ID,
            "source": "https://data.go.th/dataset/zoo-visitors2569",
            "total_records": api_result.get(
                "total", len(records)
            ),
            "returned_records": len(records),
            "data": records
        }

    except HTTPException:
        raise

    except requests.Timeout:
        raise HTTPException(
            status_code=504,
            detail="Data.go.th connection timeout"
        )

    except requests.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"Data.go.th connection error: {str(e)}"
        )
