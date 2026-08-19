from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
import sys
sys.path.append("/opt/airflow/scraper")
from hdfs_upload import upload_to_hdfs , upload_all_hdfs
from datetime import datetime 


with DAG(
    dag_id="aqarmap_scraper",
    start_date=datetime(2026, 7, 20),
    schedule_interval="@daily",
    catchup=False,
) as dag:

    scrape_task = BashOperator(
        task_id="run_scraper",
        bash_command="cd /opt/airflow/scraper && python main.py",
    )
    
    upload_task = PythonOperator(
        task_id = 'upload_hdfs'
        , python_callable = upload_all_hdfs
    )

    clean_task = SparkSubmitOperator(
        task_id='clean_id',
        application="/opt/airflow/spark_jobs/clean_listings.py",
        conn_id="spark_default",
    )
    scrape_task >> upload_task >>clean_task



