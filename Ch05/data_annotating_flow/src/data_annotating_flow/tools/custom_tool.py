from crewai.tools import tool
import os
import requests

@tool
def load_csv(input_file: str) -> str:    
    """CSV 파일을 로드하여 데이터프레임을 csv 형태로 반환합니다."""
    import pandas as pd
    print(f"\n\n\n\n\n{input_file}\n\n\n\n\n")
    df = pd.read_csv(input_file)
    print("\n\n")
    print("CSV 파일 로드 완료")
    print(df.head())
    print(f"\n\n")
    return df.to_csv(index=False)