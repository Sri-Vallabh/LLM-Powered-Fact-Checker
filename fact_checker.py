import os
import chromadb
from chromadb.utils import embedding_functions
import json
import re
from openai import OpenAI
import re
import json
import spacy
from transformers import T5ForConditionalGeneration, T5Tokenizer
from transformers import pipeline  

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
        self.client = chromadb.PersistentClient(path=chroma_path)
        self.collection = self.client.get_collection(
            name=collection_name,
            embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
        )
        self.groq_client = groq_client
        self.model_name = "llama3-8b-8192"
        self.ner = spacy.load("en_core_web_sm")
        

        self.claim_tokenizer = T5Tokenizer.from_pretrained("Babelscape/t5-base-summarization-claim-extractor")
        self.claim_model = T5ForConditionalGeneration.from_pretrained("Babelscape/t5-base-summarization-claim-extractor")

    def extract_entities(self, text):
        doc = self.ner(text)
        return [(ent.text, ent.label_) for ent in doc.ents]

    def extract_claims(self, text, threshold=0.5):
        tok_input = self.claim_tokenizer.batch_encode_plus([text], return_tensors="pt", padding=True)
        outputs = self.claim_model.generate(**tok_input)
        claims = self.claim_tokenizer.batch_decode(outputs, skip_special_tokens=True)
        claims = [claim.strip() for claim in claims if len(claim.strip()) > 0]
        return claims


    def verify_single_claim(self, claim, confidence_threshold=0.5):
        results = self.collection.query(
            query_texts=[claim],
            n_results=3,
            include=["documents", "metadatas", "distances"]
        )
        zipped_results = sorted(
            zip(results['documents'][0], results['metadatas'][0], results['distances'][0]),
            key=lambda x: x[2]
        )
        evidence = []
        for doc, meta, distance in zipped_results:
            source = meta["source"] if meta and "source" in meta else "Unknown source"
            similarity_score = 1 - (distance / 2)  # Assuming cosine distance in [0,2]
            evidence.append(
                f'"{doc}" (Source: {source}, Similarity: {similarity_score:.2f})'
            )
        avg_distance = sum(d for _, _, d in zipped_results) / len(zipped_results)
        confidence = 1 - (avg_distance / 2)  # Normalize to 0-1 range

        if confidence < confidence_threshold:
            return {
                "verdict": "Unverifiable",
                "confidence": confidence,
                "evidence": [e.split(" (Source:")[0] for e in evidence],
                "reasoning": "Claim is too vague or lacks sufficient evidence"
            }

        evidence_str = "\n".join([f"- {e}" for e in evidence])
        prompt = f"""You are a powerful fact checker. Analyze the claim below against the provided verified information. 
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
        response_content = completion.choices[0].message.content
        parsed = robust_json_extractor(response_content)
        if "error" in parsed:
            return {
                "error": parsed["error"],
                "confidence": confidence,
                "raw_response": parsed.get("raw", response_content)
            }
        else:
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

    def verify_single_entity(self, entity_text, confidence_threshold=0.5):
        """Verify a single named entity against the fact database"""
        # Vector similarity search
        results = self.collection.query(
            query_texts=[entity_text],
            n_results=3,
            include=["documents", "metadatas", "distances"]
        )
        
        # Process evidence with similarity normalization
        evidence = []
        total_distance = 0
        for doc, meta, distance in zip(results['documents'][0], 
                                    results['metadatas'][0], 
                                    results['distances'][0]):
            similarity = 1 - (distance / 2)  # Convert cosine distance to similarity
            evidence.append({
                "text": doc,
                "source": meta.get("source", "Unknown"),
                "similarity": similarity
            })
            total_distance += distance
        
        avg_similarity = 1 - (total_distance / len(results['distances'][0]) / 2)
        
        # Prepare LLM verification prompt
        evidence_str = "\n".join([
            f"- {e['text']} (Similarity: {e['similarity']:.2f})" 
            for e in evidence
        ])
        
        prompt = f"""**Entity Verification Task**
    Entity: "{entity_text}"

    **Verified Evidence:**
    {evidence_str}

    **Instructions:**
    1. Verify if this entity exists in official records
    2. Check for exact matches of names/titles
    3. Confirm associated details (locations, dates, roles)
    4. Return JSON with: verdict (True/False/Unverified), confidence (0-1), reasoning

    **JSON Response:"""
        
        try:
            response = self.groq_client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return {
                "verdict": result.get("verdict", "Unverified"),
                "confidence": min(max(result.get("confidence", avg_similarity), 0), 1),
                "evidence": [e["text"] for e in evidence],
                "reasoning": result.get("reasoning", "No reasoning provided")
            }
            
        except Exception as e:
            return {
                "verdict": "Error",
                "confidence": 0,
                "evidence": [],
                "reasoning": f"Verification failed: {str(e)}"
            }

    def verify_claim(self, text, confidence_threshold=0.5):
        """
        Main method: takes input text, extracts entities and claims, 
        verifies each, and returns JSON results
        """
        # Extract entities and claims
        entities = self.extract_entities(text)
        claims = self.extract_claims(text)
        
        # Verify claims
        claim_results = []
        for claim in claims:
            verification = self.verify_single_claim(claim, confidence_threshold)
            claim_results.append({
                "claim": claim,
                "verdict": verification.get("verdict", "Error"),
                "confidence": verification.get("confidence", 0),
                "evidence": verification.get("evidence", []),
                "reasoning": verification.get("reasoning", "Analysis failed")
            })
        
        # Verify entities
        entity_results = []
        for entity_text, entity_label in entities:
            verification = self.verify_single_entity(entity_text, confidence_threshold)
            entity_results.append({
                "entity": entity_text,
                "type": entity_label,
                "verdict": verification.get("verdict", "Error"),
                "confidence": verification.get("confidence", 0),
                "evidence": verification.get("evidence", []),
                "reasoning": verification.get("reasoning", "Analysis failed")
            })
        
        return {
            "entities": entity_results,
            "claims": claim_results
        }

