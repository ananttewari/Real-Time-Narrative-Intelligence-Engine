# Batch Narrative Intelligence Engine - User Guide

## Overview
This application is a **Batch Analytics** platform. It analyzes a static set of synthetic news articles to provide reproducible, high-quality insights for research papers.
It does **not** requires Kafka or zookeeper. It only requires Elasticsearch and Python.

## Prerequisites
1.  **Elasticsearch**: Ensure Elasticsearch is running on `http://localhost:9200`.
2.  **Python Environment**: Python 3.9+.

## Installation
1.  Navigate to the `batch_analytics` folder:
    ```bash
    cd batch_analytics
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements_batch.txt
    ```
3.  Download necessary ML models (first run only):
    ```bash
    python -m spacy download en_core_web_sm
    python -m textblob.download_corpora
    ```

## Running the Application
1.  Start the Dashboard:
    ```bash
    streamlit run batch_dashboard.py
    ```
2.  **In the Browser**:
    *   You will see an empty dashboard initially.
    *   Go to the **Sidebar**.
    *   Click **"🔄 Run Batch Simulation"**.
    *   Wait for the progress to complete (Generating 1000 articles takes ~30-60s depending on CPU).
    *   The dashboard will automatically refresh with the new data.

## Features
*   **Indian Demographic Data**: Synthetic data tailored to Indian cities and organizations.
*   **Batch Reproducibility**: High-quality, stratified dataset (92% Factual, 8% Clickbait).
*   **Advanced Analytics**: Sentiment, Geospatial, and Semantic Clustering (UMAP/KMeans).
