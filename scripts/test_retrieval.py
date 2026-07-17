import os
import sys
import logging

# Reconfigure stdout to support UTF-8 characters (like Hindi, Marathi, and Rupee symbols) on Windows
sys.stdout.reconfigure(encoding='utf-8')

# Adjust sys.path to resolve backend imports from repository root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.rag_service import rag_service

logging.basicConfig(level=logging.WARNING)

test_queries = {
    "FAQ": "What should I do if my smart device is not connecting to Wi-Fi?",
    "Products": "What are the models and features of the Nexora Smart Hub?",
    "Pricing": "What is the monthly price of the Nexora Premium Support Plan?",
    "Refunds": "How many days do I have to request a refund?",
    "Shipping": "What are the shipping delivery times for orders?",
    "Warranty": "How long is the warranty period for Nexora smart products?",
    "Installation": "How do I install the Nexora smart switch?",
    "User Guidance": "How do I reset my Nexora device to factory settings?",
    "Hindi Query": "मुझे रिफंड कितने दिनों में मिल सकता है?",
    "Marathi Query": "वाय-फाय कनेक्टिव्हिटी समस्या कशी सोडवायची?"
}

print("="*60)
print("RUNNING SEMANTIC RETRIEVAL TESTS")
print("="*60)

for category, query in test_queries.items():
    print(f"\nCategory: {category}")
    print(f"Query: '{query}'")
    try:
        # Load index and retrieve
        hits = rag_service.query_similarity(query, top_k=2)
        if not hits:
            print("  -> No results matched.")
        else:
            for i, hit in enumerate(hits):
                print(f"  Hit {i+1} [Score: {hit['similarity_score']:.4f}]:")
                print(f"    Source File: {hit['source_filename']}")
                print(f"    Title      : {hit['document_title']}")
                print(f"    Page Range : Page {hit['page_start']} to {hit['page_end']}")
                # Print first 120 characters of matched text
                snippet = " ".join(hit["text"].split())[:150] + "..."
                print(f"    Snippet    : {snippet}")
    except Exception as e:
        print(f"  -> Error executing query: {e}")

print("\n" + "="*60)
