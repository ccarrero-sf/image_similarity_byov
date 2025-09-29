# Image Similarity Search with Snowflake Cortex Search (BYOV)

This project demonstrates how to implement an image similarity search system using Snowflake's Cortex Search with "Bring Your Own Vector" (BYOV) capabilities. The demo shows how to create vector embeddings for images and build a search service to find visually similar images.

## 📓 Jupyter Notebook (`cortex_search_byov_demo.ipynb`)

The notebook provides a complete walkthrough of building an image similarity search system with the following components:

### Key Features:
- **Demo Data Generation**: Creates a collection of 100+ product images across multiple categories (Electronics, Fashion, Home & Furniture, Beauty & Health, Sports & Fitness) sourced from Unsplash
- **Snowflake Integration**: Sets up database tables, stages, and handles both local and Snowflake-native environments
- **Image Processing Pipeline**: Downloads images from URLs and stores them in Snowflake stages
- **Vector Generation**: Uses Snowflake's `AI_EMBED` function with the `voyage-multimodal-3` model to create vector embeddings for each image
- **Cortex Search Service**: Creates a multi-index search service that combines text and vector indexes for image similarity search
- **Testing & Validation**: Demonstrates querying the search service to find visually similar images

### Workflow:
1. Generate demo product image URLs from various categories
2. Create Snowflake table schema for storing image metadata
3. Download images and store them in Snowflake stages
4. Generate vector embeddings using AI_EMBED with voyage-multimodal-3 model
5. Create Cortex Search Service with vector indexes (BYOV approach)
6. Test similarity search functionality

## 🖥️ Streamlit App (`image_similarity_streamlit_app.py`)

An interactive web application that provides a user-friendly interface for image similarity search with two main modes:

### Features:
- **🖼️ Select from Stage**: Browse and select from existing processed images in the Snowflake stage
- **⬆️ Upload Image**: Upload custom images for real-time similarity search
- **🔍 AI-Powered Search**: Uses vector embeddings to find visually similar images
- **📊 Grid Display**: Shows search results in an organized, responsive grid layout
- **🎯 Interactive Interface**: Adjustable number of results, image previews, and detailed metadata

### How it Works:
1. **Image Selection**: Choose from pre-processed images or upload new ones
2. **Vector Generation**: Converts images to high-dimensional vectors using voyage-multimodal-3 model
3. **Similarity Search**: Queries the Cortex Search Service using vector distance calculations
4. **Results Display**: Shows the most similar images ranked by visual similarity scores

### Technical Implementation:
- Uses Snowflake's Core API to access Cortex Search Services
- Handles image processing with PIL for uploaded files
- Implements caching for better performance
- Provides error handling and user feedback

## 🚀 Getting Started

1. **Setup Environment**: Ensure you have Snowflake access and required Python packages
2. **Run the Notebook**: Execute `cortex_search_byov_demo.ipynb` to set up the data and search service
3. **Launch the App**: Run `streamlit run image_similarity_streamlit_app.py` to start the interactive interface

This demo showcases the power of Snowflake's Cortex Search BYOV capabilities for building sophisticated image similarity search applications.
