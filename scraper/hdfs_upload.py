import requests
import os
from datetime import date


def upload_to_hdfs(local_path, hdfs_path, namenode_url="http://namenode:9870"):
    create_url = f"{namenode_url}/webhdfs/v1{hdfs_path}?op=CREATE&overwrite=true"
    
    redirect_response = requests.put(create_url, allow_redirects=False)

    if redirect_response.status_code != 307:
        print(f"Unexpected response from namenode: {redirect_response.status_code}")
        return False

    datanode_url = redirect_response.headers["Location"]

    with open(local_path, "rb") as f:
        upload_response = requests.put(datanode_url, data=f)

    if upload_response.status_code == 201:
        print(f"Uploaded {local_path} to HDFS at {hdfs_path}")
        return True
    else:
        print(f"Upload failed: {upload_response.status_code}")
        return False 
    
def upload_all_hdfs():
    today = date.today().isoformat()
    files_to_upload = [
        (f"/opt/airflow/scraper/aqarmap_sale_{today}.jsonl", f"/bronze/aqarmap_sale_{today}.jsonl"),
        (f"/opt/airflow/scraper/aqarmap_rent_{today}.jsonl", f"/bronze/aqarmap_rent_{today}.jsonl"),
    ]
    for local_path, hdfs_path in files_to_upload:
        upload_to_hdfs(local_path, hdfs_path)