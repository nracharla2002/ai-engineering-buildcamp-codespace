import os
import urllib.request

import duckdb
import pandas as pd
from pydantic import BaseModel, Field

DATA_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet"
PARQUET_FILE = "yellow_tripdata_2024-01.parquet"

def setup_database(db_path="taxi.db", parquet_file=PARQUET_FILE):
    """Download the parquet file and load it into DuckDB."""
    if not os.path.exists(parquet_file):
        print(f"Downloading {DATA_URL}...")
        urllib.request.urlretrieve(DATA_URL, parquet_file)

    con = duckdb.connect(db_path)
    try:
        con.execute("CREATE TABLE IF NOT EXISTS trips AS SELECT * FROM read_parquet(?)", [parquet_file])
        count = con.execute("SELECT COUNT(*) FROM trips").fetchone()[0]
        print(f"Loaded {count} rows")
        return count
    finally:
        con.close()

class SQLResult(BaseModel):
    query: str = Field(description="sql query to execute ")
    result_text: str = Field(description="result of the  sql query")
    row_count: int = Field(description="number of rows the query output")
    
class RunSQLParams(BaseModel):
    query: str = Field(description="SQL query to execute")
    
class SQLTools:
    def __init__(self,db_path="taxi.db"):
        self.con = duckdb.connect(db_path)
        
    def get_schema(self):
        try:
            cursor = self.con.execute("DESCRIBE trips")
            cols = cursor.fetchall()
            return [(field, dtype) for field, dtype, *_ in cols]
        except Exception as e:
            print("Error in get_schema:", e)
            raise


    def run_sql(self, query: str) -> SQLResult:
        """Execute a SQL query and return its rows as formatted text."""
        cursor = self.con.execute(query)
        cols = [ c[0] for c in cursor.description]
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=cols)
        return SQLResult(
            query=query,
            result_text=df.to_string(),
            row_count=len(df)
        )
    
