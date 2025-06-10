import os
import chromadb
from chromadb.utils import embedding_functions
import json
import re
from openai import OpenAI
import re
import json

def robust_json_extractor(response_content):
    # Preprocess: Remove markdown code blocks and extra whitespace
    cleaned = re.sub(r'``````', '', response_content).strip()
    
    # Key-specific regex patterns
    patterns = {
        "verdict": r'"verdict"\s*:\s*"((?:\\"|[^"])*)"',
        "evidence": r'"evidence"\s*:\s*(\[[^\]]*?\]|\[.*?\])(?=\s*[,}])',
        "reasoning": r'"reasoning"\s*:\s*"((?:\\"|[^"])*)"'
    }
    
    result = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, cleaned, re.DOTALL)
        if match:
            try:
                if key == "evidence":
                    # Handle array parsing with json.loads
                    evidence_str = re.sub(r'(?<!\\)"', r'\"', match.group(1))  # Escape unescaped quotes
                    result[key] = json.loads(evidence_str)
                else:
                    # Unescape quotes for strings
                    result[key] = json.loads(f'"{match.group(1)}"')  
            except:
                # Fallback: Return raw matched string
                result[key] = match.group(1)
    
    # Validation
    required_keys = ["verdict", "evidence", "reasoning"]
    if all(key in result for key in required_keys):
        return result
    else:
        # Fallback to standard JSON parsing
        try:
            return json.loads(re.search(r'\{.*\}', cleaned, re.DOTALL).group())
        except:
            return {"error": "Failed to extract required keys", "raw": cleaned}

class FactChecker:
    def __init__(self, chroma_path, collection_name, groq_client):
        self.client = chromadb.Client()
        self.collection = self.client.get_collection(
            name=collection_name,
            embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
        )
        self.groq_client = groq_client
        self.model_name = "llama3-8b-8192"

    def verify_claim(self, claim, confidence_threshold=0.5):
    # Vector search returns full verified statements with distances
        results = self.collection.query(
            query_texts=[claim],
            n_results=3,
            include=["documents", "metadatas", "distances"]
        )
        
        # Pair documents with their distances and sort by similarity (ascending distance)
        zipped_results = sorted(
            zip(results['documents'][0], results['metadatas'][0], results['distances'][0]),
            key=lambda x: x[2]  # Sort by distance (ascending = most similar first)
        )
        
        # Format evidence with similarity scores (full sentences, not fragments)
        evidence = []
        for doc, meta, distance in zipped_results:
            source = meta["source"] if meta and "source" in meta else "Unknown source"
            # Convert distance to similarity score (higher = more similar)
            similarity_score = 1 - (distance / 2)  # Assuming cosine distance in [0,2]
            evidence.append(
                f'"{doc}" (Source: {source}, Similarity: {similarity_score:.2f})'
            )


        # Calculate overall confidence
        avg_distance = sum(d for _, _, d in zipped_results) / len(zipped_results)
        confidence = 1 - (avg_distance / 2)  # Normalize to 0-1 range

        # Threshold check
        if confidence < confidence_threshold:
            return {
                "verdict": "Unverifiable",
                "confidence": confidence,
                "evidence": [e.split(" (Source:")[0] for e in evidence],  # Cleaned evidence
                "reasoning": "Claim is too vague or lacks sufficient evidence"
            }

        # LLM verification with distance-aware prompt
        evidence_str = "\n".join([f"- {e}" for e in evidence])
        prompt = f""" You are a powerful fact checker. Analyze the claim below against the provided verified information. 
Relying on the similarity scores, also carefully check whether all factual details in the claim (such as dates, names, locations, and events) exactly match the evidence. 
If there is any factual mismatch (for example, the date in the claim is different from the evidence), classify the claim as False. Any factual mismatch, even if the overall context is similar, should lead to a False classification.
If the evidence is too vague or lacks strong matches, classify as Unverifiable.
If evidence directly contradicts the claim, classify as False.
Any discrepancy in factual details, even if the overall context is similar, should lead to a False classification.
If the evidence fully supports the claim with all factual details matching, classify as True.

Claim:
{claim}

Evidence (with similarity scores):
{evidence_str}

Guidelines:
1. Give more weight to evidence with higher similarity scores, but do not ignore factual mismatches.
2. Pay close attention to details such as dates, names, locations, and events.
3. If the claim and evidence differ on any factual point, do not classify as True.
4. Respond only in JSON format without any additional text.
5. In the "evidence" array, include only full evidence statements as strings, without any extra comments or explanations.
6. Put all explanations or comparisons in the "reasoning" field.

Respond in JSON format:
{{
    "verdict": "Verdict",
    "evidence": [List of relevant facts from provided evidence],
    "reasoning": "Explanation of the verdict based on evidence and factual details"
}}
"""

        
        completion = self.groq_client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=400
        )
        
        # Process response
        response_content = completion.choices[0].message.content
        print(f"Response from Groq: {response_content}")

        # Use the robust JSON extractor
        parsed = robust_json_extractor(response_content)
        print(f"Parsed JSON: {parsed}")

        if "error" in parsed:
            return {
                "error": parsed["error"],
                "confidence": confidence,
                "raw_response": parsed.get("raw", response_content)
            }
        else:
            # Validate required fields
            required_keys = ["verdict", "evidence", "reasoning"]
            if all(key in parsed for key in required_keys):
                return {
                    "verdict": parsed["verdict"],
                    "confidence": confidence,
                    "evidence": [e.split(" (Source:")[0] for e in evidence],
                    "reasoning": parsed["reasoning"]
                }
            else:
                return {
                    "error": f"Missing required keys: {[k for k in required_keys if k not in parsed]}",
                    "confidence": confidence,
                    "raw_response": response_content
                }