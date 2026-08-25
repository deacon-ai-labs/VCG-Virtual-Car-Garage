from pathlib import Path 

  

import pymupdf 

from openai import OpenAI 

  

from database import get_supabase_client 

  

  

KNOWLEDGE_DIR = Path("knowledge") 

  

CHUNK_SIZE = 1400 

CHUNK_OVERLAP = 200 

  

EMBEDDING_MODEL = "text-embedding-3-small" 

EMBEDDING_BATCH_SIZE = 50 

DATABASE_BATCH_SIZE = 100 

  

  

DOCUMENTS = { 

    "honda_civic_2004_owners_manual.pdf": { 

        "source_name": "Honda Civic 2004 Owner's Manual", 

        "source_type": "owners_manual", 

        "vehicle_scope": "civic_3door_all_models", 

    }, 

    "honda_civic_type_r_2004_specs.pdf": { 

        "source_name": "Honda Civic Type R 2004 Specifications", 

        "source_type": "technical_specification", 

        "vehicle_scope": "civic_type_r_ep3", 

    }, 

    "honda_civic_type_r_2004_press_release.pdf": { 

        "source_name": "Honda Civic Type R 2004 Press Release", 

        "source_type": "press_release", 

        "vehicle_scope": "civic_type_r_ep3", 

    }, 

} 

  

  

def split_text(text: str) -> list[str]: 

    """Split text into overlapping chunks.""" 

  

    text = " ".join(text.split()) 

  

    if not text: 

        return [] 

  

    chunks = [] 

    start = 0 

  

    while start < len(text): 

        end = start + CHUNK_SIZE 

        chunk = text[start:end].strip() 

  

        if chunk: 

            chunks.append(chunk) 

  

        if end >= len(text): 

            break 

  

        start = end - CHUNK_OVERLAP 

  

    return chunks 

  

  

def extract_chunks() -> list[dict]: 

    """Extract page text from each PDF and create chunk records.""" 

  

    chunks = [] 

  

    for filename, metadata in DOCUMENTS.items(): 

        pdf_path = KNOWLEDGE_DIR / filename 

  

        if not pdf_path.exists(): 

            raise FileNotFoundError( 

                f"Could not find {pdf_path}" 

            ) 

  

        print(f"\nReading {filename}...") 

  

        document = pymupdf.open(pdf_path) 

  

        try: 

            for page_index, page in enumerate(document): 

                page_text = page.get_text("text") or "" 

  

                page_chunks = split_text(page_text) 

  

                for chunk in page_chunks: 

                    chunks.append( 

                        { 

                            "source_name": metadata["source_name"], 

                            "source_type": metadata["source_type"], 

                            "vehicle_scope": metadata["vehicle_scope"], 

                            "page_number": page_index + 1, 

                            "content": chunk, 

                        } 

                    ) 

  

            print( 

                f"Finished {filename}: " 

                f"{len(document)} pages" 

            ) 

  

        finally: 

            document.close() 

  

    return chunks 

  

  

def add_embeddings(chunks: list[dict]) -> list[dict]: 

    """Create an embedding for every knowledge chunk.""" 

  

    client = OpenAI() 

  

    total = len(chunks) 

  

    for start in range(0, total, EMBEDDING_BATCH_SIZE): 

        batch = chunks[ 

            start:start + EMBEDDING_BATCH_SIZE 

        ] 

  

        texts = [ 

            chunk["content"] 

            for chunk in batch 

        ] 

  

        response = client.embeddings.create( 

            model=EMBEDDING_MODEL, 

            input=texts, 

        ) 

  

        for chunk, embedding_result in zip( 

            batch, 

            response.data, 

        ): 

            chunk["embedding"] = embedding_result.embedding 

  

        completed = min( 

            start + EMBEDDING_BATCH_SIZE, 

            total, 

        ) 

  

        print( 

            f"Created embeddings: " 

            f"{completed}/{total}" 

        ) 

  

    return chunks 

  

  

def clear_existing_documents() -> None: 

    """Remove previous copies of these documents.""" 

  

    supabase = get_supabase_client() 

  

    for metadata in DOCUMENTS.values(): 

        ( 

            supabase.table("knowledge_chunks") 

            .delete() 

            .eq( 

                "source_name", 

                metadata["source_name"], 

            ) 

            .execute() 

        ) 

  

  

def save_chunks(chunks: list[dict]) -> None: 

    """Insert knowledge chunks into Supabase.""" 

  

    supabase = get_supabase_client() 

  

    total = len(chunks) 

  

    for start in range(0, total, DATABASE_BATCH_SIZE): 

        batch = chunks[ 

            start:start + DATABASE_BATCH_SIZE 

        ] 

  

        ( 

            supabase.table("knowledge_chunks") 

            .insert(batch) 

            .execute() 

        ) 

  

        completed = min( 

            start + DATABASE_BATCH_SIZE, 

            total, 

        ) 

  

        print( 

            f"Saved to Supabase: " 

            f"{completed}/{total}" 

        ) 

  

  

def main(): 

    print("Virtual Car Garage knowledge ingestion") 

    print("--------------------------------------") 

  

    chunks = extract_chunks() 

  

    print( 

        f"\nCreated {len(chunks)} text chunks." 

    ) 

  

    if not chunks: 

        raise RuntimeError( 

            "No knowledge chunks were extracted." 

        ) 

  

    source_types = sorted( 

        { 

            chunk["source_type"] 

            for chunk in chunks 

        } 

    ) 

  

    print( 

        "\nSource types found: " 

        + ", ".join(source_types) 

    ) 

  

    expected_source_types = { 

        "owners_manual", 

        "technical_specification", 

        "press_release", 

    } 

  

    missing_source_types = ( 

        expected_source_types 

        - set(source_types) 

    ) 

  

    if missing_source_types: 

        raise RuntimeError( 

            "Missing extracted source types: " 

            + ", ".join( 

                sorted(missing_source_types) 

            ) 

        ) 

  

    print("\nCreating OpenAI embeddings...") 

    chunks = add_embeddings(chunks) 

  

    print("\nRemoving previous copies...") 

    clear_existing_documents() 

  

    print("\nSaving knowledge to Supabase...") 

    save_chunks(chunks) 

  

    print("\nKnowledge ingestion complete.") 

  

  

if __name__ == "__main__": 

    main() 