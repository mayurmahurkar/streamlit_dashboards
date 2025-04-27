import os
from math import ceil
import os.path as osp
from PIL import ImageFile,Image
ImageFile.LOAD_TRUNCATED_IMAGES = True
import streamlit as st
from natsort import natsorted
import yaml
import sys
import os
import itertools

# Get the absolute path to the root directory of your project
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from utils.image_displayer_utils import *

config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
with open(config_path, "r") as config_file:
    config = yaml.safe_load(config_file)

st.set_page_config(
    layout="wide", 
    page_title="The Sharingan - Image Displayer",
    initial_sidebar_state="expanded",
    page_icon="⭕️",
)

st.image('sharingan.png', width=700)
st.divider()

# @st.cache_data(show_spinner=True)
def display_images_in_grid(images, num_columns = 3, resize_dim = None, thumbnail_size = None):
    
    if natural_sort:
        natsorted(images)
    else:
        images.sort()
    
    num_columns = int(num_columns)
    num_images = len(images)
    num_rows = (num_images + num_columns - 1) // num_columns

    for i in range(num_rows):
        cols = st.columns(num_columns)
        for j in range(num_columns):
            image_index = i * num_columns + j
            if image_index < num_images:
                image_path = images[image_index]
                img = Image.open(image_path)
                if resize_dim:
                    img = img.resize(resize_dim, Image.Resampling.LANCZOS)
                if thumbnail_size:
                    img.thumbnail((thumbnail_size, thumbnail_size))
                # cols[j].image(img, use_column_width=True, caption=osp.basename(image_path))
                cols[j].image(img, use_container_width=True, caption=osp.basename(image_path)) # to supress warning

imgs_dir_path = st.sidebar.text_input("Input Images Directory Path")
rescursive_search = st.sidebar.toggle('Recursive Search')

########################################################################
natural_sort = False
if config["natural_sort"]:
    natural_sort = st.sidebar.toggle('Natural Sort')
    st.sidebar.info("Natural sorting is the ordering of strings in alphabetical order,\nexcept that multi-digit numbers are treated atomically, i.e., as if they were a single character. _https://stackoverflow.com/questions/5167928/what-is-natural-ordering-when-we-talk-about-sorting_") 
########################################################################
# thumbnail_size = st.sidebar.number_input("Re-Scale Images by percentage", min_value=100, max_value=2000, step = 200)
# thumbnail_size = st.sidebar.text_input("Re-Scale Images by percentage")
thumbnail_size = None

resize_dim = st.sidebar.text_input("Input New Image Dimesions: (_width_, _height_)")
st.sidebar.divider()

if thumbnail_size:
    thumbnail_size = eval(thumbnail_size)
else:
    thumbnail_size = None

if resize_dim:
    resize_dim = eval(resize_dim)
else:
    resize_dim = None

st.session_state.folder_path = imgs_dir_path

if not (os.path.exists(imgs_dir_path) and os.path.isdir(imgs_dir_path)):
    st.error(f"Images directory path is wrong or isn't directory: {imgs_dir_path}")

else:
    if rescursive_search: 
        all_imgs = [os.path.join(root, file) for root, _, files in os.walk(st.session_state.folder_path) for file in files if is_image_file(file)]

    else:
        all_imgs = []
        for img_file_pth in os.listdir(st.session_state.folder_path):
            if img_file_pth.lower().endswith(('.png', '.jpg', '.jpeg')):
                all_imgs.append(os.path.join(st.session_state.folder_path, img_file_pth))

    if len(all_imgs) == 0:
        st.error(f"No images found in: {imgs_dir_path}, make sure 'Recursive Search' is ON if you are expecting images within directory(s) of the input path.")
    
    else:
        st.sidebar.write("Total images:", len(all_imgs))
        num_columns = st.sidebar.number_input("No. of images per row", min_value=1, max_value=10, value = config["num_columns"])

        ###################################################################################################################################
        imgs_per_page = st.sidebar.number_input("No. of images per page", min_value=100, max_value=1000, value = config["imgs_per_page"], step = 100)
        ###################################################################################################################################
        all_imgs.sort()
        
        # Initialize the current page in session state if it doesn't exist
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 0
            
        # Calculate total pages
        total_pages = ceil(len(all_imgs)/imgs_per_page)
        
        # Get current page from paginator and update session state
        location = st.sidebar.empty()
        page_format_func = lambda i: f"Page {i+1}"
        st.session_state.current_page = location.selectbox(
            f"Select a page from < **{total_pages}** > pages", 
            range(total_pages), 
            index=st.session_state.current_page,
            format_func=page_format_func,
            key="page_selector"
        )
        
        # Get images for current page
        min_index = st.session_state.current_page * imgs_per_page
        max_index = min_index + imgs_per_page
        image_iterator = list(itertools.islice(enumerate(all_imgs), min_index, max_index))
        
        indices_on_page, images_on_page = map(list, zip(*image_iterator)) if image_iterator else ([], [])
        
        # Display images
        display_images_in_grid(images_on_page, num_columns, resize_dim, thumbnail_size)
        
        # Add pagination buttons at the bottom
        st.sidebar.write("Current Page:", st.session_state.current_page + 1)
        
        # Next/Previous buttons at the bottom of page
        left_col, middle_col, right_col = st.columns([1, 10, 1])
        
        # Previous button on left
        if left_col.button("⬅️ Previous Page", disabled=(st.session_state.current_page <= 0)):
            st.session_state.current_page = max(0, st.session_state.current_page - 1)
            st.rerun()
            
        # Next button on right
        if right_col.button("➡️ Next Page", disabled=(st.session_state.current_page >= total_pages - 1)):
            st.session_state.current_page = min(total_pages - 1, st.session_state.current_page + 1)
            st.rerun()

if __name__ == "__main__":
    pass