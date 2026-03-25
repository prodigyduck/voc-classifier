import psycopg2
from psycopg2 import sql
import yaml
from pathlib import Path


def load_config():
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def create_tables():
    config = load_config()
    db_config = config["database"]

    conn = psycopg2.connect(
        host=db_config["host"],
        port=db_config["port"],
        dbname=db_config["name"],
        user=db_config["user"],
        password=db_config["password"]
    )
    conn.autocommit = True
    cursor = conn.cursor()

    with open(Path(__file__).parent / "schema.sql", "r", encoding="utf-8") as f:
        sql_script = f.read()

    try:
        cursor.execute(sql_script)
        print("테이블이 성공적으로 생성되었습니다.")
    except Exception as e:
        print(f"테이블 생성 중 오류 발생: {e}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    create_tables()
