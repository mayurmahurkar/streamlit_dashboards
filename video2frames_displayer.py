import os
import streamlit as st
from datetime import timedelta
import cv2

# st.set_page_config(layout="wide")

def capture_video_frames(video_path):
    # Open and Capture the video file
    return cv2.VideoCapture(video_path)


def get_video_info(video_capture):

    # Get video details
    fps = int(video_capture.get(cv2.CAP_PROP_FPS))
    width = int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

    return fps, width, height

def main():

    # Sidebar for folder path input
    folder_path = st.sidebar.text_input("Input Videos Directory Path:")
    st.session_state.folder_path = folder_path

    if not (os.path.exists(folder_path) and os.path.isdir(folder_path)):
        st.error(f"Videos directory path is wrong or isn't directory: {folder_path}")
    
    else:
        # Get list of video files in the folder
        video_files = [file for file in os.listdir(folder_path) if file.endswith((".mp4", ".avi"))]
        video_files.sort()
        if len(video_files) == 0:
            st.error(f"No videos found in: {folder_path}.")

        # Dropdown menu to select video file
        selected_video = st.sidebar.selectbox("Select video file:", video_files)
        
        st.sidebar.divider()
        show_ms = st.sidebar.toggle("Show Milliseconds")

        if selected_video:
            
            # Read the selected video file
            video_path = os.path.join(folder_path, selected_video)
            video_capture = capture_video_frames(video_path)
            
            total_frames = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_num = st.slider("Select Frame No.:", 0, total_frames - 1, 0)

            # Get video information
            video_name = os.path.basename(video_path)
            fps, width, height = get_video_info(video_capture)

            # Display video frames
            video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            _, frame = video_capture.read()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Calculate the total duration of the video in seconds
            total_duration_seconds = total_frames / fps

            # Calculate the elapsed time for the current frame
            elapsed_time_seconds = frame_num / fps
            elapsed_minutes = int(elapsed_time_seconds // 60)
            elapsed_seconds = int(elapsed_time_seconds % 60)

            if show_ms:
                elapsed_milliseconds = int((elapsed_time_seconds - int(elapsed_time_seconds)) * 1000)
                st.write(f":stopwatch:    {str(elapsed_minutes)} : {str(elapsed_seconds)} : {str(elapsed_milliseconds)}")

            else:
                st.write(f":stopwatch:    {str(elapsed_minutes)} : {str(elapsed_seconds)}")

            st.image(frame, caption= f"{video_name}")
            # st.write(f"Current Frame: {frame_num}")
            # Release the video capture object
            video_capture.release()

            # Display additional information
            # st.sidebar.write(f"Video Name: {video_name}")
            st.sidebar.write(f"FPS: {fps}")
            st.sidebar.write(f"Resolution: {width} x {height}")

if __name__ == "__main__":
    main()