import chromadb
import uuid
import os
import numpy as np
from PIL import Image  # Used to open and process images
from chromadb.config import Settings
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction
from chromadb.utils.data_loaders import ImageLoader

class ChromaDBUtility:
    def __init__(self, db_dir="chromadb_data"):
        """
        Initialize ChromaDB with a multi-modal collection.
        """
        db_dir = os.path.abspath(db_dir)  # Ensure path is absolute
        self.client = chromadb.PersistentClient(path=db_dir)

        embedding_function = OpenCLIPEmbeddingFunction()
        data_loader = ImageLoader()

        self.collection = self.client.get_or_create_collection(
            name="planos_multimodal",
            embedding_function=embedding_function,
            data_loader=data_loader
        )

    def add_text_document(self, text, metadata={}):
        """
        Add a plain text document with metadata.
        """
        doc_id = str(uuid.uuid4())
        if "description" not in metadata:
            metadata["description"] = text
        self.collection.add(
            ids=[doc_id],
            documents=[text],
            metadatas=[metadata]
        )
        return doc_id

    def add_image(self, image_path, description="", metadata={}):
        """
        Legacy single-call method – not used in multimodal update.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        if "path" in metadata and os.path.isabs(metadata["path"]):
            metadata["path"] = os.path.relpath(metadata["path"], os.getcwd())

        img_id = str(uuid.uuid4())
        self.collection.add(
            ids=[img_id],
            uris=[image_path],
            documents=[description],
            metadatas=[metadata]
        )
        return img_id

    def add_image_with_text(self, image_path, description="", metadata={}):
        """
        Two-step image + optional text embedding.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        if "path" in metadata and os.path.isabs(metadata["path"]):
            metadata["path"] = os.path.relpath(metadata["path"], os.getcwd())
        if "description" not in metadata:
            metadata["description"] = description or os.path.basename(image_path)

        record_id = str(uuid.uuid4())
        self.collection.add(
            ids=[record_id],
            documents=[metadata["description"]],
            metadatas=[metadata]
        )
        self.collection.update(
            ids=[record_id],
            uris=[image_path]
        )
        return record_id

    def search_by_text(self, query_text, n_results=5):
        """
        Full-text embedding search.
        """
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            include=["metadatas", "documents", "distances"]
        )
        return self._format_results(results)

    def search_by_image(self, image_path, n_results=5):
        """
        Image similarity search (using image file as input).
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        with Image.open(image_path) as img:
            img_array = np.array(img.convert('RGB'))

        results = self.collection.query(
            query_images=[img_array],
            n_results=n_results,
            include=["metadatas", "documents", "distances"]
        )
        return self._format_results(results)

    def search_by_uri(self, uri, n_results=5):
        """
        Search for similar items using an external URI.
        """
        results = self.collection.query(
            query_uris=[uri],
            n_results=n_results,
            include=["metadatas", "documents", "distances"]
        )
        return self._format_results(results)

    def _format_results(self, results):
        """
        Helper to format search results.
        """
        matches = []
        if results.get("ids"):
            for i, item_id in enumerate(results["ids"][0]):
                doc = results["documents"][0][i] if "documents" in results and results["documents"] else ""
                metadata = results["metadatas"][0][i] if "metadatas" in results and results["metadatas"] else {}
                distance = results["distances"][0][i] if "distances" in results and results["distances"] else None
                matches.append({
                    "id": item_id,
                    "document": doc,
                    "metadata": metadata,
                    "distance": distance
                })
        return matches

    def get_all_files(self):
        """
        Retrieve all stored files from ChromaDB.
        """
        results = self.collection.peek()
        files = []
        if results and 'ids' in results and results['ids']:
            for i, file_id in enumerate(results['ids']):
                metadata = results['metadatas'][i] if 'metadatas' in results and results['metadatas'] else {}
                files.append({
                    "id": file_id,
                    "filename": metadata.get('filename', 'Unknown'),
                    "path": metadata.get('path', 'No Path Available')
                })
        return files

    def get_file_metadata(self, file_id):
        """
        Fetch metadata for a given file ID.
        """
        try:
            result = self.collection.get(ids=[file_id])
            if result and "metadatas" in result and result["metadatas"]:
                return result["metadatas"][0]
        except Exception as e:
            print(f"[ERROR] Failed to fetch metadata: {e}")
        return None

    def delete_file(self, file_id):
        """
        Delete a file from ChromaDB and disk (if applicable).
        """
        metadata = self.get_file_metadata(file_id)
        if metadata and "path" in metadata:
            try:
                full_path = os.path.join(os.getcwd(), metadata["path"])
                if os.path.exists(full_path):
                    os.remove(full_path)
            except Exception as e:
                print(f"[WARN] Could not delete file from disk: {e}")

        self.collection.delete(ids=[file_id])


# Initialize ChromaDB Utility
chroma_db = ChromaDBUtility()
