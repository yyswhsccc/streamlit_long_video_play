import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import random
import os

# Constants and configuration
SHEET_ID = '1jESaEV_iK5GSuO2WDV8RTcDzP42WmDIE4dAIei7yYFU'
RANGE_NAME = 'high quality 100k feedback'
SERVICE_ACCOUNT_FILE = 'caption-comparison-3dd6dfcad088.json'
num_ids = 133943

# Initialize Google Sheets API
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
service = build('sheets', 'v4', credentials=credentials)
sheet = service.spreadsheets()

# def get_image_and_captions(id):
#     # 构建视频文件名
#     video_filename = f"{id:08d}.mp4"
#     video_url = f"http://localhost:8050/{video_filename}"

#     # 从CSV文件中读取GPT 4V caption
#     metadata_df = pd.read_csv("/home/ec2-user/info.csv", header=0)
#     # 确保ID格式与CSV中的video_id一致
#     video_id_str = f"{video_filename}"
#     gpt4v_caption_row = metadata_df[metadata_df['video_id'] == video_id_str]

#     if not gpt4v_caption_row.empty:
#         gpt4v_caption = gpt4v_caption_row['captions'].iloc[0]
#     else:
#         gpt4v_caption = "This video does not have a caption."

#     return video_url, gpt4v_caption

# 按照00000000-99999999进行读取
def get_image_and_captions(id):
    # 构建视频文件名
    video_filename = f"{id:08d}.mp4"
    # video_url = f"http://localhost:8093/{video_filename}"
    
    video_url = f"http://54.176.199.228//videos/{video_filename}"

    # 假设所有文件都存在并且没有附带的 caption
    return video_url, None

# 按照文件名本身 进行读取
# def get_image_and_captions(id, csv_path):
#     # 从CSV文件中读取视频文件名
#     csv_path = 'video_filenames.csv'
    
#     df = pd.read_csv(csv_path)
#     if id < len(df):
#         video_filename = df.loc[id, 'filename']
#         video_url = f"http://54.176.199.228/videos/{video_filename}"
#     else:
#         # 如果ID无效，返回错误信息
#         video_url = "Invalid video ID"
    
#     return video_url, None

# def get_image_and_captions(id):
#     try:
#         # 读取CSV文件
#         csv_file_path = 'rename_log_mira.csv'  # 确保这里是CSV文件的正确路径
#         rename_log = pd.read_csv(csv_file_path)
        
#         # 确保ID在有效范围内
#         if id >= 0 and id < len(rename_log):
#             video_filename = rename_log['New Name'].iloc[id]
#             video_url = f"http://54.176.199.228//videos/{video_filename}"
#             return video_url, None
#         else:
#             return "Invalid video ID", None  # 返回一个错误消息而不是None
#     except Exception as e:
#         # 处理可能的错误，例如文件找不到或读取CSV失败
#         print(f"Error accessing video data: {str(e)}")
#         return "Error loading video data", None  # 返回错误消息

import streamlit as st
from datetime import datetime

# Ensure to set up your Google Sheets API and credentials
# RANGE_NAME and SHEET_ID should be defined here or imported
# Also, define `sheet` which represents the Google Sheets API client.

# 加载视频时长数据
def load_video_data(csv_path):
    df = pd.read_csv(csv_path)
    return df

def plot_cdf(video_data, video_filename):
    durations = video_data['duration'].sort_values().values
    # 计算累积分布
    values, base = np.histogram(durations, bins=40, weights=np.ones(len(durations)) / len(durations))
    cumulative = np.cumsum(values)

    plt.figure(figsize=(12, 2))
    plt.plot(base[:-1], cumulative, c='blue')
    
    # 根据视频文件名直接找到当前视频的时长
    if video_filename in video_data['video_id'].values:
        current_duration = video_data[video_data['video_id'] == video_filename]['duration'].values[0]
        # 标注当前视频的位置
        plt.scatter(current_duration, np.interp(current_duration, base[:-1], cumulative), color='red')
    else:
        print("Video filename not found in duration data.")

    plt.title('Video Duration Distribution')
    plt.xlabel('Duration (seconds)')
    plt.ylabel('CDF')
    plt.grid(True)


def save_score_to_sheet(id, score, reviewer_name, reason):
    row_index = id + 3  # Assuming data starts from the third row, id is a 0-based index

    score_cell = f"{RANGE_NAME}!E{row_index}"
    current_scores = sheet.values().get(spreadsheetId=SHEET_ID, range=score_cell).execute().get('values', [['']])[0][0]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Process existing scores
    all_scores = current_scores.split('\n')
    user_scores = {}
    for s in all_scores:
        if ':' in s:
            name, rest = s.split(':', 1)
            user_scores[name.strip()] = rest.strip()
    
    # Update with the new score
    user_scores[reviewer_name] = f"{score} at {timestamp}"
    
    # Convert back to the final string for storage
    final_scores = '\n'.join([f"{name}: {s}" for name, s in user_scores.items()])
    score_value = [{'range': score_cell, 'values': [[final_scores]]}]
    body = {'valueInputOption': 'USER_ENTERED', 'data': score_value}
    sheet.values().batchUpdate(spreadsheetId=SHEET_ID, body=body).execute()

    # Update the rating reason
    reason_cell = f"{RANGE_NAME}!G{row_index}"
    current_reasons = sheet.values().get(spreadsheetId=SHEET_ID, range=reason_cell).execute().get('values', [['']])[0][0]
    # Process existing reasons
    all_reasons = current_reasons.split('\n')
    user_reasons = {}
    for r in all_reasons:
        if ':' in r:
            name, rest = r.split(':', 1)
            user_reasons[name.strip()] = rest.strip()

    # Update with the new reason
    user_reasons[reviewer_name] = f"{reason}, at {timestamp}"

    # Convert back to the final string for storage
    final_reasons = '\n'.join([f"{name}: {r}" for name, r in user_reasons.items()])
    reason_value = [{'range': reason_cell, 'values': [[final_reasons]]}]
    reason_body = {'valueInputOption': 'USER_ENTERED', 'data': reason_value}
    sheet.values().batchUpdate(spreadsheetId=SHEET_ID, body=reason_body).execute()

    # Update the history
    history_cell = f"{RANGE_NAME}!F{row_index}"
    current_history = sheet.values().get(spreadsheetId=SHEET_ID, range=history_cell).execute().get('values', [['']])[0][0]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_history = f"{current_history}\n{reviewer_name}: {score} at {timestamp}".strip()
    history_value = [{'range': history_cell, 'values': [[new_history]]}]
    history_body = {'valueInputOption': 'USER_ENTERED', 'data': history_value}
    sheet.values().batchUpdate(spreadsheetId=SHEET_ID, body=history_body).execute()

    # Calculate the average score based on the latest scores
    total_score = 0
    for s in user_scores.values():
        score_value = float(s.split(' ')[0])
        total_score += score_value
    average_score = total_score / len(user_scores)

    num_raters = len(user_scores)
    
    # Update the average score in column C
    result_cell = f"{RANGE_NAME}!D{row_index}"
    result_value = [{'range': result_cell, 'values': [[f"{average_score:.2f}\nNumber of raters: {num_raters}"]]}]
    result_body = {'valueInputOption': 'USER_ENTERED', 'data': result_value}
    sheet.values().batchUpdate(spreadsheetId=SHEET_ID, body=result_body).execute()

def submit(id, score, reviewer_name, reason):
    # Check if the reviewer name or reason is missing and display a prominent error message
    if not reviewer_name:
        st.error("Error: You must enter your name to rate this video. Please enter your name below.")
        return False  # Return None to stop the execution of the function here
    # if not reason:
    #     st.error("Error: You must provide a reason for your rating. Please enter your reason below.")
    #     return False  # Return None to stop the execution of the function here
    save_score_to_sheet(id, score, reviewer_name, reason)
    return True

def main():
    st.title("Data Rating Tool")
    st.write("Please rate this video to decide whether it should remain in our dataset.")

    video_data = load_video_data('video_durations.csv')

    if "video_index" not in st.session_state:
        st.session_state["video_index"] = 0

    ids = list(range(len(video_data)))  # 确保下拉菜单与数据行对应
    id_dropdown = st.selectbox("Choose Data ID", ids, index=st.session_state["video_index"])

    # 更新视频索引
    st.session_state["video_index"] = id_dropdown
    video_index = st.session_state["video_index"]
    video_url, _ = get_image_and_captions(video_index)

    # 从视频URL中提取文件名
    video_filename = video_url.split('/')[-1]

    plot_cdf(video_data, video_filename)
    st.pyplot(plt)  # 显示图表

    st.write(video_url)  # Assuming this prints the video URL, you might replace it with st.video(video_url) for actual videos

    # Navigation and progress bar
    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
    with col1:
        if st.button("Previous Video"):
            if video_index > 0:
                st.session_state["video_index"] -= 1
                st.experimental_rerun()
            else:
                st.warning('This is the first video.')
    with col2:
        if st.button("Next Video"):
            if video_index < num_ids - 1:
                st.session_state["video_index"] += 1
                st.experimental_rerun()
            else:
                st.warning('This is the last video.')

    with col3:
        if st.button('Random Video'):
            random_id = random.randint(0, num_ids - 1)
            st.session_state['video_index'] = random_id
            st.experimental_rerun()
            
    with col4:
        progress = video_index / num_ids
        st.progress(progress)
        
    # Rating interface
    score_input = st.slider("Rate the video (1: Terrible, 3: Pass, 5: High quality)", 1, 5, value=3)
    reviewer_name_input = st.text_input("Your Name", placeholder="Enter your name...")
    reason_input = st.text_area("Write your feedback (NOT MANDATORY) ", placeholder="Enter your reason for rating...")

    if st.button("Submit Rating"):
        result = submit(video_index, score_input, reviewer_name_input, reason_input)
        if result:
            st.success("Rating and reason saved successfully.")

if __name__ == "__main__":
    main()
