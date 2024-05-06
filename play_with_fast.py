import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import pandas as pd
from datetime import datetime

# Constants and configuration
SHEET_ID = '1jESaEV_iK5GSuO2WDV8RTcDzP42WmDIE4dAIei7yYFU'
RANGE_NAME = 'Sheet1'
SERVICE_ACCOUNT_FILE = 'caption-comparison-3dd6dfcad088.json'
num_ids = 2000

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
    video_url = f"http://localhost:8091/{video_filename}"

    # 假设所有文件都存在并且没有附带的 caption
    return video_url, None


import streamlit as st
from datetime import datetime

# Ensure to set up your Google Sheets API and credentials
# RANGE_NAME and SHEET_ID should be defined here or imported
# Also, define `sheet` which represents the Google Sheets API client.

def save_vote_to_sheet(id, vote, reviewer_name, reason):
    row_index = id + 2  # Assuming data starts from the third row, id is a 0-based index

    vote_cell = f"{RANGE_NAME}!D{row_index}"
    current_votes = sheet.values().get(spreadsheetId=SHEET_ID, range=vote_cell).execute().get('values', [['']])[0][0]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Process existing votes
    all_votes = current_votes.split('\n')
    user_votes = {}
    for v in all_votes:
        if ':' in v:
            name, rest = v.split(':', 1)
            user_votes[name.strip()] = rest.strip()
    
    # Update with the new vote
    user_votes[reviewer_name] = f"{vote} at {timestamp}"
    
    # Convert back to the final string for storage
    final_votes = '\n'.join([f"{name}: {v}" for name, v in user_votes.items()])
    vote_value = [{'range': vote_cell, 'values': [[final_votes]]}]
    body = {'valueInputOption': 'USER_ENTERED', 'data': vote_value}
    sheet.values().batchUpdate(spreadsheetId=SHEET_ID, body=body).execute()

    # Update the history
    history_cell = f"E{row_index}"
    current_history = sheet.values().get(spreadsheetId=SHEET_ID, range=history_cell).execute().get('values', [['']])[0][0]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_history = f"{current_history}\n{reviewer_name}: {vote} at {timestamp}".strip()
    history_value = [{'range': history_cell, 'values': [[new_history]]}]
    history_body = {'valueInputOption': 'USER_ENTERED', 'data': history_value}
    sheet.values().batchUpdate(spreadsheetId=SHEET_ID, body=history_body).execute()

    # Update the rating reason
    reason_cell = f"F{row_index}"
    current_reason = sheet.values().get(spreadsheetId=SHEET_ID, range=reason_cell).execute().get('values', [['']])[0][0]
    new_reason = f"{current_reason}\n{reviewer_name}: {reason}, at {timestamp}".strip()
    reason_value = [{'range': reason_cell, 'values': [[new_reason]]}]
    reason_body = {'valueInputOption': 'USER_ENTERED', 'data': reason_value}
    sheet.values().batchUpdate(spreadsheetId=SHEET_ID, body=reason_body).execute()

    # Calculate the final result based on latest votes
    yes_votes = sum(1 for v in user_votes.values() if 'Yes' in v)
    total_votes = len(user_votes)
    result = "Keep" if yes_votes / total_votes > 0.6 else "No"

    # Update result in column C
    result_cell = f"{RANGE_NAME}!C{row_index}"
    result_value = [{'range': result_cell, 'values': [[result]]}]
    result_body = {'valueInputOption': 'USER_ENTERED', 'data': result_value}
    sheet.values().batchUpdate(spreadsheetId=SHEET_ID, body=result_body).execute()


def submit(id, vote, reviewer_name, reason):
    if not reviewer_name:
        return "Please enter your name to vote on this video."
    if not reason:
        return "Please provide a reason for your vote."
    save_vote_to_sheet(id, vote, reviewer_name, reason)
    return "Vote and reason saved successfully."


def main():
    st.title("Data Voting Tool")
    st.write("Please vote to decide whether this video should remain in our dataset.")

    ids = list(range(num_ids))
    id_dropdown = st.selectbox("Choose Data ID", ids)

    # Get only the video URL from the returned tuple
    video_url, _ = get_image_and_captions(id_dropdown)
    
    # Display video based on selected data ID
    st.video(video_url)

    vote_input = st.radio("Please vote", ["Yes", "No"])
    reviewer_name_input = st.text_input("Your Name", placeholder="Enter your name...")
    reason_input = st.text_area("Voting Reason", placeholder="Enter your reason for voting...")

    if st.button("Submit Voting"):
        result = submit(id_dropdown, vote_input, reviewer_name_input, reason_input)
        st.write(result)

if __name__ == "__main__":
    main()


