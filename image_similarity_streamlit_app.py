
import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session
from snowflake.core import Root
import requests
from PIL import Image
import io
import tempfile
import os
import json

# Get Snowflake session
session = get_active_session()

# App configuration
st.set_page_config(
    page_title="🔍 Image Similarity Search",
    page_icon="🖼️",
    layout="wide"
)

st.title("🔍 Image Similarity Search")
st.markdown("Find visually similar images using AI-powered vector search")

# Table and stage configuration
TABLE_NAME_DOWNLOADED_VECT = "IMAGES_TABLE_DOWNLOADED_VECT"
STAGE_NAME = "IMAGES"

# Query Cortex Search function (embedded in app)
def query_cortex_search(query_text, query_vector, top_k):
    """
    Query the multi-index Cortex Search Service with emphasis on vector similarity using Snowflake Core API.
    """
    try:
        # Use Snowflake Core API to access the Cortex Search Service
        root = Root(session)
        
        # Fetch the Cortex Search Service
        my_service = (root
          .databases["CC_IMAGES_POC"]
          .schemas["PUBLIC"]
          .cortex_search_services["IMAGES_CS_SERVICE"]
        )
        
        # Query service using multi-index syntax with vector emphasis
        resp = my_service.search(
            multi_index_query={
                # Vector index query for image similarity
                "image_vector": [{"vector": query_vector}]
            },
            columns=["source_id", "original_url", "stage_file_path"],  # Specify columns to return
            limit=top_k
        )
        
        # Convert results to the expected format for the Streamlit app
        results = []
        for result in resp.results:
            result_dict = {
                'SOURCE_ID': result.get('source_id', 'N/A'),
                'ORIGINAL_URL': result.get('original_url', ''), 
                'STAGE_FILE_PATH': result.get('stage_file_path', 'N/A')
            }
            results.append(result_dict)
            
        return results
        
    except Exception as e:
        st.error(f"Search error: {e}")
        # Add more detailed error info for debugging
        st.error(f"Query text: {query_text}")
        st.error(f"Vector length: {len(query_vector) if hasattr(query_vector, '__len__') else 'Unknown'}")
        return []

# Helper function to get available images from staging area
@st.cache_data
def get_available_images():
    """Get list of available images from the vectorization table"""
    try:
        query = f"""
        SELECT 
            SOURCE_ID,
            ORIGINAL_URL,
            STAGE_FILE_PATH,
            IMAGE_VECTOR
        FROM {TABLE_NAME_DOWNLOADED_VECT}
        ORDER BY SOURCE_ID
        """
        result = session.sql(query).collect()
        return result
    except Exception as e:
        st.error(f"Error loading images: {e}")
        return []

# Helper function to display images in a grid
def display_image_grid(results, query_info=None):
    """Display search results in a responsive grid"""
    if not results:
        st.warning("No results to display")
        return
    
    # Display query image if provided
    if query_info:
        st.subheader("🎯 Query Image")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            try:
                if query_info.get('uploaded_image'):
                    st.image(query_info['uploaded_image'], caption="Uploaded Image", use_container_width=True)
                else:
                    st.image(query_info['url'], caption=f"Query: {query_info.get('file_path', 'Unknown')}", use_container_width=True)
            except Exception as e:
                st.error(f"Error displaying query image: {e}")
    
    st.subheader(f"📊 Top {len(results)} Similar Images")
    
    # Create responsive columns (3 per row)
    cols_per_row = 3
    for i in range(0, len(results), cols_per_row):
        cols = st.columns(cols_per_row)
        
        for j, result in enumerate(results[i:i+cols_per_row]):
            with cols[j]:
                try:
                    source_id = result.get('SOURCE_ID', 'N/A')
                    url = result.get('ORIGINAL_URL', '')
                    file_path = result.get('STAGE_FILE_PATH', 'N/A')
                    
                    if url:
                        st.image(url, caption=f"#{i+j+1}: ID {source_id}\n{file_path}", use_container_width=True)
                    else:
                        st.error(f"No URL for result #{i+j+1}")
                        
                except Exception as e:
                    st.error(f"Error loading image #{i+j+1}: {e}")

# Main app interface
tab1, tab2 = st.tabs(["🖼️ Select from Stage", "⬆️ Upload Image"])

# Tab 1: Select from existing images
with tab1:
    st.header("Select an Image from Staging Area")
    
    # Load available images
    available_images = get_available_images()
    
    if available_images:
        # Create selection interface
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Available Images")
            
            # Create a selectbox with image info
            image_options = {
                f"ID {img['SOURCE_ID']}: {img['STAGE_FILE_PATH']}": img 
                for img in available_images
            }
            
            selected_option = st.selectbox(
                "Choose an image:",
                list(image_options.keys()),
                help="Select an image to find similar ones"
            )
            
            # Search parameters
            top_k = st.slider("Number of results", 1, 10, 5)
            
            search_button = st.button("🔍 Find Similar Images", type="primary")
        
        with col2:
            if selected_option:
                selected_image = image_options[selected_option]
                st.subheader("Selected Image Preview")
                
                try:
                    # Display selected image
                    st.image(
                        selected_image['ORIGINAL_URL'], 
                        caption=f"ID {selected_image['SOURCE_ID']}: {selected_image['STAGE_FILE_PATH']}",
                        use_container_width=True
                    )
                    
                    # Show image info
                    st.info(f"""
                    **Image Information:**
                    - Source ID: {selected_image['SOURCE_ID']}
                    - File: {selected_image['STAGE_FILE_PATH']}
                    - Vector dimensions: {len(selected_image['IMAGE_VECTOR'])}
                    """)
                    
                except Exception as e:
                    st.error(f"Error displaying selected image: {e}")
        
        # Perform search when button is clicked
        if search_button and selected_option:
            selected_image = image_options[selected_option]
            
            with st.spinner("🔍 Searching for similar images..."):
                try:
                    # Call the search function
                    results = query_cortex_search(
                        query_text=selected_image['ORIGINAL_URL'],
                        query_vector=selected_image['IMAGE_VECTOR'],
                        top_k=top_k
                    )
                    
                    # Display results
                    query_info = {
                        'url': selected_image['ORIGINAL_URL'],
                        'file_path': selected_image['STAGE_FILE_PATH'],
                        'source_id': selected_image['SOURCE_ID']
                    }
                    
                    display_image_grid(results, query_info)
                    
                    st.success(f"✅ Found {len(results)} similar images!")
                    
                except Exception as e:
                    st.error(f"❌ Search failed: {e}")
    else:
        st.warning("No images found in the staging area. Please check the vectorization table.")

# Tab 2: Upload custom image
with tab2:
    st.header("Upload Your Own Image")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose an image file",
            type=['png', 'jpg', 'jpeg', 'gif', 'bmp'],
            help="Upload an image to find similar ones"
        )
        
        if uploaded_file:
            # Search parameters
            top_k_upload = st.slider("Number of results", 1, 20, 10, key="upload_top_k")
            search_upload_button = st.button("🔍 Find Similar Images", type="primary", key="upload_search")
    
    with col2:
        if uploaded_file:
            st.subheader("Uploaded Image Preview")
            
            try:
                # Display uploaded image
                image = Image.open(uploaded_file)
                st.image(image, caption=f"Uploaded: {uploaded_file.name}", use_container_width=True)
                
                # Show file info
                st.info(f"""
                **File Information:**
                - Name: {uploaded_file.name}
                - Size: {len(uploaded_file.getvalue())} bytes
                - Type: {uploaded_file.type}
                """)
                
            except Exception as e:
                st.error(f"Error displaying uploaded image: {e}")
    
    # Process uploaded image search
    if uploaded_file and search_upload_button:
        with st.spinner("🔄 Processing uploaded image and searching..."):
            try:
                # Create temporary file for the uploaded image
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpeg') as tmp_file:
                    # Save uploaded image
                    image = Image.open(uploaded_file)
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                    image.save(tmp_file.name, 'JPEG')
                    
                    # Upload to Snowflake stage
                    session.file.put(
                        tmp_file.name,
                        f"@{STAGE_NAME}/temp/",
                        overwrite=True,
                        auto_compress=False
                    )
                    
                    temp_filename = os.path.basename(tmp_file.name)
                    
                    # Generate vector for uploaded image
                    vector_query = f"""
                    SELECT AI_EMBED('voyage-multimodal-3', TO_FILE('@{STAGE_NAME}/temp/{temp_filename}')) as image_vector
                    """
                    vector_result = session.sql(vector_query).collect()
                    
                    if vector_result:
                        uploaded_vector = vector_result[0]['IMAGE_VECTOR']
                        
                        # Search for similar images
                        results = query_cortex_search(
                            query_text=uploaded_file.name,  # Use filename as text query
                            query_vector=uploaded_vector,
                            top_k=top_k_upload
                        )
                        
                        # Display results
                        query_info = {
                            'uploaded_image': image,
                            'file_path': uploaded_file.name
                        }
                        
                        display_image_grid(results, query_info)
                        
                        st.success(f"✅ Found {len(results)} similar images!")
                        
                        # Note: Leaving temp file in stage (cleanup not critical)
                    
                    # Clean up local temp file
                    os.unlink(tmp_file.name)
                    
            except Exception as e:
                st.error(f"❌ Upload search failed: {e}")
                # Clean up local temp file on error
                try:
                    if 'tmp_file' in locals() and os.path.exists(tmp_file.name):
                        os.unlink(tmp_file.name)
                except:
                    pass

# Sidebar with app info
with st.sidebar:
    st.header("ℹ️ App Information")
    st.markdown("""
    **Image Similarity Search App**
    
    This app uses AI-powered vector embeddings to find visually similar images.
    
    **Features:**
    - 🖼️ **Select from Stage**: Choose from existing processed images
    - ⬆️ **Upload Image**: Upload your own image for comparison
    - 🎯 **Vector Search**: Uses voyage-multimodal-3 model for embeddings
    - 📊 **Visual Results**: Display similar images in an organized grid
    
    **How it works:**
    1. Images are converted to high-dimensional vectors
    2. Similarity is calculated using vector distance
    3. Results are ranked by visual similarity
    """)
    
    # Display current configuration
    st.markdown("---")
    st.markdown("**Configuration:**")
    st.code(f"""
Database: CC_IMAGES_POC
Schema: PUBLIC
Stage: {STAGE_NAME}
Search Service: IMAGES_CS_SERVICE
Vector Table: {TABLE_NAME_DOWNLOADED_VECT}
    """)
