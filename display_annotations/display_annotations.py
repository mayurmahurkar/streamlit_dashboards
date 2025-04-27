import os
from math import ceil, sqrt
import os.path as osp
from PIL import ImageFile, Image, ImageDraw, ImageFont
ImageFile.LOAD_TRUNCATED_IMAGES = True
import streamlit as st
from natsort import natsorted
import numpy as np
import colorsys
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
    page_title="The Sharingan - Annotation Displayer",
    initial_sidebar_state="expanded",
    page_icon="⭕️", 
)

st.image('sharingan.png', width=700)
st.divider()

# Initialize color mapping in session state if it doesn't exist
if 'color_map' not in st.session_state:
    st.session_state.color_map = {}
if 'used_colors' not in st.session_state:
    st.session_state.used_colors = []

def color_distance(c1, c2):
    return sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))

def is_similar(c1, c2, threshold=50):
    return color_distance(c1, c2) < threshold

def _generate_unique_bold_color():
    max_attempts = 1000
    np.random.seed(42)
    for _ in range(max_attempts):
        h = np.random.rand()
        r, g, b = colorsys.hsv_to_rgb(h, 0.9, 1.0)
        color = (int(r * 255), int(g * 255), int(b * 255))
        if all(not is_similar(color, used) for used in st.session_state.used_colors):
            st.session_state.used_colors.append(color)
            return color
    # Fallback if no distinct color found
    fallback = tuple(np.random.randint(0, 255, 3))
    st.session_state.used_colors.append(fallback)
    return fallback

def get_color_for_class(class_id):
    if class_id in st.session_state.color_map:
        return st.session_state.color_map[class_id]
    color = _generate_unique_bold_color()
    st.session_state.color_map[class_id] = color
    return color

def display_annotations_in_grid(images, num_columns=3, resize_dim=None, thumbnail_size=None):
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
                image_name = osp.splitext(osp.basename(image_path))[0]
                label_path = osp.join(labels_dir_path, image_name + ".txt")

                img = Image.open(image_path).convert("RGB")
                draw = ImageDraw.Draw(img)
                img_width, img_height = img.size

                thickness = max(1, img_height // 300)
                font_size = max(10, img_height // 40)

                try:
                    font = ImageFont.truetype("arial.ttf", font_size)
                except:
                    font = ImageFont.load_default()

                if osp.exists(label_path):
                    with open(label_path, 'r') as f:
                        for line in f:
                            parts = line.strip().split()
                            if len(parts) != 5:
                                continue
                            cls_id, x_center, y_center, width, height = map(float, parts)
                            x1 = int((x_center - width / 2) * img_width)
                            y1 = int((y_center - height / 2) * img_height)
                            x2 = int((x_center + width / 2) * img_width)
                            y2 = int((y_center + height / 2) * img_height)

                            color = get_color_for_class(int(cls_id))
                            draw.rectangle([x1, y1, x2, y2], outline=color, width=thickness)

                            # Determine label text
                            if label_names and 0 <= int(cls_id) < len(label_names):
                                label = label_names[int(cls_id)]
                            else:
                                label = str(int(cls_id))

                            text_bbox = font.getbbox(label)
                            text_width = text_bbox[2] - text_bbox[0]
                            text_height = text_bbox[3] - text_bbox[1]

                            # Label box background
                            label_bg = [x1, y1, x1 + text_width + 6, y1 + text_height + 4]
                            draw.rectangle(label_bg, fill=color)
                            draw.text((x1 + 3, y1 + 2), label, fill="white", font=font)
                else:
                    text = "NO LABELS FOUND"
                    font_size = max(20, img_height // 15)  # Font size is proportional to image height (you can adjust the divisor for your liking)
                    try:
                        font = ImageFont.truetype("arial.ttf", font_size)
                    except:
                        font = ImageFont.load_default()

                    text_bbox = font.getbbox(text)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]

                    box_x = (img_width - text_width) // 2
                    box_y = 10
                    box_padding = 10  # Increased padding for better readability
                    box_coords = [
                        (box_x - box_padding, box_y - box_padding),
                        (box_x + text_width + box_padding, box_y + text_height + box_padding)
                    ]

                    draw.rectangle(box_coords, fill=(139, 0, 0))  # Dark red background
                    draw.text((box_x, box_y), text, fill="white", font=font)

                if resize_dim:
                    img = img.resize(resize_dim, Image.Resampling.LANCZOS)
                if thumbnail_size:
                    img.thumbnail((thumbnail_size, thumbnail_size))

                if use_original_img_width:
                    cols[j].image(img, width=img.width, caption=osp.basename(image_path))
                else:
                    cols[j].image(img, use_container_width=True, caption=osp.basename(image_path))


# Sidebar Inputs
imgs_dir_path = st.sidebar.text_input("Input Images Directory Path")
labels_dir_path = st.sidebar.text_input("Input Labels Directory Path (optional)")
yaml_path = st.sidebar.text_input("Input dataset.yaml path (optional)")

label_names = None
if yaml_path:
    if osp.exists(yaml_path):
        try:
            with open(yaml_path, 'r') as yf:
                yaml_dict = yaml.safe_load(yf)
                label_names = yaml_dict.get('names', None)
                if not isinstance(label_names, (list, tuple)):
                    st.sidebar.error('Invalid "names" format in YAML; expected a list.')
                    label_names = None
        except Exception as e:
            st.sidebar.error(f"Error loading YAML: {e}")
            label_names = None
    else:
        st.sidebar.error(f"YAML file not found: {yaml_path}")

natural_sort = False
if config["natural_sort"]:
    natural_sort = st.sidebar.toggle('Natural Sort')
    st.sidebar.info("Natural sorting is the ordering of strings in alphabetical order,\nexcept that multi-digit numbers are treated atomically, i.e., as if they were a single character.")

use_original_img_width = st.sidebar.toggle('Original Image Width')
resize_dim = None 
thumbnail_size = None
    
if not use_original_img_width:
    # thumbnail_size = st.sidebar.text_input("Re-Scale Images by percentage")
    resize_dim = st.sidebar.text_input("Input New Image Dimesions: (_width_, _height_)")
    st.sidebar.divider()

    # Parse values
    if thumbnail_size:
        thumbnail_size = eval(thumbnail_size)
    else:
        thumbnail_size = None

    if resize_dim:
        resize_dim = eval(resize_dim)
    else:
        resize_dim = None

if not labels_dir_path:
    labels_dir_path = osp.join(imgs_dir_path, "..", "labels")
    st.sidebar.write(f"Derived Labels Directory Path: {labels_dir_path}")

st.session_state.folder_path = imgs_dir_path

if not (os.path.exists(imgs_dir_path) and os.path.isdir(imgs_dir_path)):
    st.error(f"Images directory path is wrong or isn't directory: {imgs_dir_path}")

else:
    all_imgs = []
    for img_file_pth in os.listdir(st.session_state.folder_path):
        if img_file_pth.lower().endswith(('.png', '.jpg', '.jpeg')):
            all_imgs.append(os.path.join(st.session_state.folder_path, img_file_pth))

    if len(all_imgs) == 0:
        st.error(f"No images found in: {imgs_dir_path}")
    
    else:
        st.sidebar.write("Total images:", len(all_imgs))
        num_columns = st.sidebar.number_input("No. of images per row", min_value=1, max_value=10, value = config["num_columns"])
        imgs_per_page = st.sidebar.number_input("No. of images per page", min_value=50, max_value=1000, value = config["imgs_per_page"], step = 50)
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
        display_annotations_in_grid(images_on_page, num_columns, resize_dim, thumbnail_size)

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