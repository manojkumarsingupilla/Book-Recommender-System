from flask import Flask, request, jsonify
import pickle
import os
import numpy as np
import sys
from difflib import get_close_matches

from books_recommender.logger.log import logging
from books_recommender.config.configuration import AppConfiguration
from books_recommender.pipeline.training_pipeline import TrainingPipeline
from books_recommender.exception.exception_handler import AppException

app = Flask(__name__)

# -------------------------------------------------
# Load Global Data (once at startup or after training)
# -------------------------------------------------
FINAL_RATING_PATH = os.path.join("artifacts", "serialized_objects", "final_rating.pkl")

def load_final_rating():
    try:
        data = pickle.load(open(FINAL_RATING_PATH, "rb"))
        logging.info("Loaded final_rating.pkl successfully!")
        return data
    except FileNotFoundError:
        logging.warning("final_rating.pkl not found. Please run training first.")
        return None

final_rating = load_final_rating()

# -------------------------------------------------
# Recommendation Class
# -------------------------------------------------
class Recommendation:
    def __init__(self, app_config=AppConfiguration()):
        try:
            self.recommendation_config = app_config.get_recommendation_config()
        except Exception as e:
            raise AppException(e, sys) from e

    def fetch_poster(self, suggestion):
        try:
            book_name = []
            ids_index = []
            poster_url = []

            book_pivot = pickle.load(
                open(self.recommendation_config.book_pivot_serialized_objects, "rb")
            )
            final_rating_local = pickle.load(
                open(self.recommendation_config.final_rating_serialized_objects, "rb")
            )

            for book_id in suggestion:
                book_name.append(book_pivot.index[book_id])

            for name in book_name[0]:
                ids = np.where(final_rating_local["title"] == name)[0][0]
                ids_index.append(ids)

            for idx in ids_index:
                url = final_rating_local.iloc[idx]["image_url"]
                poster_url.append(url)

            return poster_url

        except Exception as e:
            raise AppException(e, sys) from e

    def recommend_book(self, book_name):
        try:
            model = pickle.load(open(self.recommendation_config.trained_model_path, "rb"))
            book_pivot = pickle.load(open(self.recommendation_config.book_pivot_serialized_objects, "rb"))
            final_rating_local = pickle.load(open(self.recommendation_config.final_rating_serialized_objects, "rb"))

            # -----------------------------
            # 1️⃣ Exact match: KNN
            # -----------------------------
            if book_name in book_pivot.index:
                book_id = np.where(book_pivot.index == book_name)[0][0]
                distance, suggestion = model.kneighbors(
                    book_pivot.iloc[book_id, :].values.reshape(1, -1), n_neighbors=6
                )

                books_list, poster_url = [], []
                for i in range(len(suggestion)):
                    books = book_pivot.index[suggestion[i]]
                    for j in books:
                        books_list.append(j)
                        try:
                            idx = np.where(final_rating_local["title"] == j)[0][0]
                            poster_url.append(final_rating_local.iloc[idx]["image_url"])
                        except IndexError:
                            poster_url.append("URL not available")

                return books_list[1:], poster_url[1:], None  # skip input book

            # -----------------------------
            # 2️⃣ Book not found: suggestions
            # -----------------------------
            # Substring match first
            substring_matches = [title for title in book_pivot.index if book_name.lower() in title.lower()]

            # Fuzzy match (cutoff 0.6 to reduce unrelated matches)
            from difflib import get_close_matches
            fuzzy_matches = get_close_matches(book_name, book_pivot.index, n=5, cutoff=0.6)

            # Combine, remove duplicates, limit 5
            all_suggestions = list(dict.fromkeys(substring_matches + fuzzy_matches))[:5]

            # Fetch posters for suggestions if available
            poster_urls = []
            for title in all_suggestions:
                try:
                    idx = np.where(final_rating_local["title"] == title)[0][0]
                    poster_urls.append(final_rating_local.iloc[idx]["image_url"])
                except IndexError:
                    poster_urls.append("URL not available")

            if all_suggestions:
                return None, poster_urls, all_suggestions

            # -----------------------------
            # 3️⃣ No matches found
            # -----------------------------
            return None, [], []

        except Exception as e:
            raise AppException(e, sys) from e



    def train_engine(self):
        try:
            obj = TrainingPipeline()
            obj.start_training_pipeline()
            logging.info("Training completed successfully!")
            return {"message": "Training Completed!"}
        except Exception as e:
            raise AppException(e, sys) from e

# Initialize recommender
recommender = Recommendation()

# -------------------------------------------------
# Flask Routes
# -------------------------------------------------
@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Welcome to Manoj's Book Recommender API!"})

@app.route("/train", methods=["POST"])
def train():
    result = recommender.train_engine()
    global final_rating
    final_rating = load_final_rating()
    return jsonify(result)

@app.route("/recommend", methods=["POST"])
def recommend():
    try:
        data = request.get_json()
        book_name = data.get("book_name")

        if not book_name:
            return jsonify({"error": "Please provide a book_name"}), 400

        if final_rating is None:
            return jsonify({"error": "Recommendation engine is not ready. Please run training first."}), 500

        recommended_books, poster_urls, suggestions = recommender.recommend_book(book_name)

        if suggestions:  # book not found, return suggestions
            return jsonify({
                "error": f"Do you mean '{book_name}'?",
                "suggestions": suggestions,
                "poster_urls": poster_urls
            })

        return jsonify({
            "input_book": book_name,
            "recommended_books": recommended_books,
            "poster_urls": poster_urls
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------
# Run App
# -------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8501, debug=True)
