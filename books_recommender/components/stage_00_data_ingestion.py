import os
import sys
import zipfile
import requests
from books_recommender.logger.log import logging
from books_recommender.exception.exception_handler import AppException
from books_recommender.config.configuration import AppConfiguration


class DataIngestion:
    def __init__(self, app_config: AppConfiguration = AppConfiguration()):
        """
        DataIngestion Initialization
        Responsible for downloading and extracting the dataset.
        """
        try:
            logging.info(f"{'=' * 20} Data Ingestion log started. {'=' * 20}")
            self.data_ingestion_config = app_config.get_data_ingestion_config()
        except Exception as e:
            raise AppException(e, sys) from e

    def download_data(self) -> str:
        """
        Fetch the data from the dataset URL and save it as a zip file.

        Returns:
            str: Path to the downloaded zip file
        """
        try:
            dataset_url = self.data_ingestion_config.dataset_download_url
            zip_download_dir = self.data_ingestion_config.raw_data_dir
            os.makedirs(zip_download_dir, exist_ok=True)

            data_file_name = os.path.basename(dataset_url)
            zip_file_path = os.path.join(zip_download_dir, data_file_name)

            logging.info(f"Downloading data from {dataset_url} into file {zip_file_path}")

            response = requests.get(dataset_url, stream=True)
            response.raise_for_status()  # Raise exception for bad HTTP status codes

            with open(zip_file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            logging.info(f"Downloaded data from {dataset_url} into file {zip_file_path}")
            return zip_file_path

        except Exception as e:
            raise AppException(e, sys) from e

    def extract_zip_file(self, zip_file_path: str):
        """
        Extracts the zip file into the ingested directory.

        Args:
            zip_file_path (str): Path to the downloaded zip file
        """
        try:
            ingested_dir = self.data_ingestion_config.ingested_dir
            os.makedirs(ingested_dir, exist_ok=True)

            with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
                zip_ref.extractall(ingested_dir)

            logging.info(f"Extracted zip file: {zip_file_path} into dir: {ingested_dir}")

        except Exception as e:
            raise AppException(e, sys) from e

    def initiate_data_ingestion(self):
        """
        Initiates the data ingestion process:
        1. Downloads the dataset
        2. Extracts the dataset
        """
        try:
            zip_file_path = self.download_data()
            self.extract_zip_file(zip_file_path=zip_file_path)
            logging.info(f"{'=' * 20} Data Ingestion log completed. {'=' * 20}\n\n")
        except Exception as e:
            raise AppException(e, sys) from e
