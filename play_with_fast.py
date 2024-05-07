import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import pandas as pd
from datetime import datetime

# Constants and configuration
SHEET_ID = '1jESaEV_iK5GSuO2WDV8RTcDzP42WmDIE4dAIei7yYFU'
RANGE_NAME = 'Sheet1'
SERVICE_ACCOUNT_FILE = 'caption-comparison-3dd6dfcad088.json'
num_ids = 100

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

def get_image_and_captions(id):
    # 构建视频文件名
    video_filename = f"{id:08d}.mp4"
    # video_url = f"http://localhost:8093/{video_filename}"
    
    video_url = f"http://54.176.199.228/videos/{video_filename}"

    # 假设所有文件都存在并且没有附带的 caption
    return video_url, None


import streamlit as st
from datetime import datetime

# Ensure to set up your Google Sheets API and credentials
# RANGE_NAME and SHEET_ID should be defined here or imported
# Also, define `sheet` which represents the Google Sheets API client.

def save_score_to_sheet(id, score, reviewer_name, reason):
    row_index = id + 122  # Assuming data starts from the 122 row, id is a 0-based index

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

    # Update the history
    history_cell = f"F{row_index}"
    current_history = sheet.values().get(spreadsheetId=SHEET_ID, range=history_cell).execute().get('values', [['']])[0][0]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_history = f"{current_history}\n{reviewer_name}: {score} at {timestamp}".strip()
    history_value = [{'range': history_cell, 'values': [[new_history]]}]
    history_body = {'valueInputOption': 'USER_ENTERED', 'data': history_value}
    sheet.values().batchUpdate(spreadsheetId=SHEET_ID, body=history_body).execute()

    # Update the rating reason
    reason_cell = f"G{row_index}"
    current_reason = sheet.values().get(spreadsheetId=SHEET_ID, range=reason_cell).execute().get('values', [['']])[0][0]
    new_reason = f"{current_reason}\n{reviewer_name}: {reason}, at {timestamp}".strip()
    reason_value = [{'range': reason_cell, 'values': [[new_reason]]}]
    reason_body = {'valueInputOption': 'USER_ENTERED', 'data': reason_value}
    sheet.values().batchUpdate(spreadsheetId=SHEET_ID, body=reason_body).execute()

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
    if not reviewer_name:
        return "Please enter your name to rate this video."
    if not reason:
        return "Please provide a reason for your rating."
    save_score_to_sheet(id, score, reviewer_name, reason)
    return "Rating and reason saved successfully."

def main():
    st.title("Data Rating Tool")
    st.write("Please rate this video to decide whether it should remain in our dataset.")

    ids = list(range(num_ids))
    id_dropdown = st.selectbox("Choose Data ID", ids)

    # Get only the video URL from the returned tuple
    video_url, _ = get_image_and_captions(id_dropdown)
    
    # Display video based on selected data ID
    # st.video(video_url)

    st.write(video_url)

    score_input = st.slider("Rate the video (1: Terrible, 3: Pass, 5: High quality)", 1, 5, value=3)
    reviewer_name_input = st.text_input("Your Name", placeholder="Enter your name...")
    reason_input = st.text_area("Rating Reason", placeholder="Enter your reason for rating...")

    if st.button("Submit Rating"):
        result = submit(id_dropdown, score_input, reviewer_name_input, reason_input)
        st.write(result)

if __name__ == "__main__":
    main()

