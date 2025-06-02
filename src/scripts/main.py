from fastapi import FastAPI, HTTPException, Query
from typing import List
from config import get_connection
from models import (
    ResultInDB, ResultCreate, ResultUpdate,
    SessionResultLinkInDB, SessionResultLinkCreate
)

app = FastAPI(title="Lab4 RESTful API")


# ======== HELPER FUNCTIONS ==========

def fetch_all(table: str):
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        # Для таблиці Queue переіменовуємо
        if table.lower() == "queue":
            for row in rows:
                row["content_id"] = row.pop("Content_id")
        # Для таблиці SessionResultLink також переіменовуємо ключі
        if table.lower() == "sessionresultlink":
            for row in rows:
                # row має ключі "Session_id", "Session_Account_id", "Result_id"
                row["session_id"] = row.pop("Session_id")
                row["session_account_id"] = row.pop("Session_Account_id")
                row["result_id"] = row.pop("Result_id")
        return rows


def fetch_by_id(table: str, key: str, value: int):
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM {table} WHERE {key} = %s", (value,))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail=f"{table.capitalize()} not found")
        if table.lower() == "queue":
            result["content_id"] = result.pop("Content_id")
        return result


def insert_data(query: str, values: tuple):
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(query, values)
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))


def update_data(table: str, key: str, value: int, update_data: dict):
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    fields = ', '.join(f"{k} = %s" for k in update_data)
    query = f"UPDATE {table} SET {fields} WHERE {key} = %s"
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(query, list(update_data.values()) + [value])
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))


def delete_by_id(table: str, key: str, value: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(f"DELETE FROM {table} WHERE {key} = %s", (value,))
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail=f"{table.capitalize()} not found")
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))


# ========== RESULT ENDPOINTS ===========
@app.get("/result", response_model=List[ResultInDB], tags=["Result"])
async def get_all_results():
    return fetch_all("Result")


@app.get("/result/{result_id}", response_model=ResultInDB, tags=["Result"])
async def get_result(result_id: int):
    return fetch_by_id("Result", "id", result_id)


@app.post("/result", response_model=dict, status_code=201, tags=["Result"])
async def create_result(item: ResultCreate):
    insert_data(
        "INSERT INTO Result (session, notes, score) VALUES (%s, %s, %s)",
        (item.session, item.notes, item.score)
    )
    return {"message": "Result added"}


@app.put("/result/{result_id}", response_model=ResultInDB, tags=["Result"])
async def update_result(result_id: int, result_update: ResultUpdate):
    update_data("Result", "id", result_id, result_update.model_dump(exclude_unset=True))
    return await get_result(result_id)


@app.delete("/result/{result_id}", response_model=dict, tags=["Result"])
async def delete_result(result_id: int):
    delete_by_id("Result", "id", result_id)
    return {"message": f"Result with id {result_id} deleted"}


# ========== SESSIONRESULTLINK ENDPOINTS ===========
@app.get("/sessionresultlink", response_model=List[SessionResultLinkInDB], tags=["SessionResultLink"])
async def get_all_session_result_links():
    return fetch_all("SessionResultLink")


@app.post("/sessionresultlink", response_model=dict, status_code=201, tags=["SessionResultLink"])
async def create_session_result_link(link: SessionResultLinkCreate):
    insert_data(
        "INSERT INTO SessionResultLink (Session_id, Session_Account_id, Result_id) VALUES (%s, %s, %s)",
        (link.session_id, link.session_account_id, link.result_id)
    )
    return {"message": "SessionResultLink added"}


@app.delete("/sessionresultlink", response_model=dict, tags=["SessionResultLink"])
async def delete_session_result_link(
    session_id: int = Query(...),
    session_account_id: int = Query(...),
    result_id: int = Query(...)
):
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM SessionResultLink WHERE Session_id = %s AND Session_Account_id = %s AND Result_id = %s",
                (session_id, session_account_id, result_id)
            )
            conn.commit()
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="SessionResultLink not found")
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))
    return {"message": "SessionResultLink deleted"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
