from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
import itertools
import streamlit as st

def paginator(label, items, items_per_page=200, on_sidebar=True):

    # Figure out where to display the paginator
    if on_sidebar:
        location = st.sidebar.empty()
    else:
        location = st.empty()

    # Display a pagination selectbox in the specified location.
    items = list(items)
    n_pages = len(items)
    n_pages = (len(items) - 1) // items_per_page + 1
    
    # n_pages = ceil(len(all_imgs)/imgs_per_page)

    page_format_func = lambda i: "Page %s" % (i+1)
    page_number = location.selectbox(label, range(n_pages), format_func=page_format_func)

    # Iterate over the items in the page to let the user display them.
    min_index = page_number * items_per_page
    max_index = min_index + items_per_page
    return page_number, itertools.islice(enumerate(items), min_index, max_index)

def resize_by_percentage(image, percentage):
    width, height = image.size
    resized_dimensions = (int(width * percentage), int(height * percentage))
    return image.resize(resized_dimensions)

def is_image_file(filename):
    # Check if the file has a common image extension
    return any(filename.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff'])