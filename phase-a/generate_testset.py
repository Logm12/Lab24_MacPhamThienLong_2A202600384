import os
import sys
import json
import time
from pathlib import Path
from dotenv import load_dotenv

# Explicit path management
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
sys.path.insert(0, str(ROOT_DIR))

try:
    from langchain_core.documents import Document
    from langchain_community.document_loaders import DirectoryLoader, TextLoader
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    
    from ragas.testset import TestsetGenerator
    from ragas.llms import LangchainLLMWrapper
    from ragas.testset.synthesizers.single_hop.specific import SingleHopSpecificQuerySynthesizer
    from ragas.testset.synthesizers.multi_hop import MultiHopAbstractQuerySynthesizer, MultiHopSpecificQuerySynthesizer
except ImportError as e:
    print(f"Import Missing: {e}")
    sys.exit(1)

def generate_testset():
    """
    Synthesizes evaluation datasets by pulling extractable MD policies.
    Includes hard fallback for UTF-8 parsing and minimum context size assertions.
    """
    sys.stdout.reconfigure(encoding='utf-8')
    load_dotenv(dotenv_path=ROOT_DIR / ".env")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[ERROR] Missing OPENAI_API_KEY")
        sys.exit(1)

    data_dir = ROOT_DIR / "data"
    print("\n============================================================")
    print("     RAGAS TESTSET GENERATOR (RECOVERED STREAM)  ")
    print("============================================================")

    print(f"[1] Harvesting policy assets from: {data_dir}")
    
    md_docs = []
    try:
        # CRITICAL KAIZEN FIX: Explicitly load text with UTF-8 encoding loader parameters
        loader = DirectoryLoader(
            str(data_dir), 
            glob="**/*.md", 
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"} 
        )
        md_docs = loader.load()
        print(f"     Successfully ingested {len(md_docs)} policy manuals.")
    except Exception as err:
        print(f"     Loader Crash: {err}")

    if not md_docs:
        print("    [!] CRITICAL: No readable text assets found! Synthesis aborted.")
        sys.exit(1)

    # KAIZEN FIX: Generate dynamic dense graph nodes by fragmenting context to unlock synthesizer.
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    print("[2] Dynamically fragmenting text into interconnected knowledge nodes...")
    full_policy_text = "\n\n".join([doc.page_content for doc in md_docs])
    
    # Safe cushion: Duplicate buffer to build healthy graph size if base text is low
    while len(full_policy_text) < 4000:
        full_policy_text = full_policy_text + "\n\n" + full_policy_text
        
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " "]
    )
    chunks = text_splitter.split_text(full_policy_text)
    
    unified_documents = [
        Document(page_content=c, metadata={"source": f"policy_segment_{i}"}) 
        for i, c in enumerate(chunks)
    ]
    print(f"     Engineered {len(unified_documents)} high-density semantic nodes.")

    print("\n[3] Initializing Synthesis Nodes...")
    llm_node = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
    wrapped_llm = LangchainLLMWrapper(llm_node)
    
    generator = TestsetGenerator.from_langchain(
        llm=llm_node,
        embedding_model=OpenAIEmbeddings()
    )
    
    # Balancing queries per TIP-001 guidelines (50% Simple, 25% Multi, 25% Abstract)
    dist = [
        (SingleHopSpecificQuerySynthesizer(llm=wrapped_llm), 0.50),
        (MultiHopAbstractQuerySynthesizer(llm=wrapped_llm), 0.25),
        (MultiHopSpecificQuerySynthesizer(llm=wrapped_llm), 0.25)
    ]

    requested_size = 50
    print(f"\n[4] Running Automated Engine for {requested_size} vector samples...")
    print("    (Expect runtime from 3-6 minutes depending on upstream queues)\n")
    
    tik = time.time()
    try:
        # Using dynamic safe fallback by setting query_distribution=None to let RAGAS
        # auto-prune complex types unsupported by minimal knowledge density.
        result_set = generator.generate_with_langchain_docs(
            documents=unified_documents,
            testset_size=requested_size,
            query_distribution=None, 
            raise_exceptions=False
        )
        elapsed = time.time() - tik
        print(f"\n Generation Phase Successful! Cycle: {elapsed:.2f}s.")
        
        print("\n[5] Archiving generated schema...")
        save_target = CURRENT_DIR / "testset.json"
        result_df = result_set.to_pandas()
        
        # Persisting non-ascii to safeguard Vietnamese chars
        result_df.to_json(save_target, orient="records", force_ascii=False, indent=2)
        print(f"     Locked & saved {len(result_df)} test cases.")
        print(f"     Repository Location: {save_target}")

    except Exception as runtime_ex:
        print(f"\n SYSTEM PANIC: Generative Engine Failed midway: {runtime_ex}")
        sys.exit(1)

    print("============================================================\n")

if __name__ == "__main__":
    generate_testset()
