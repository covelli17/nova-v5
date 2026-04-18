"""Smoke test Gemini — librería google-genai"""
import os
from google import genai

api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    print("ERROR: GOOGLE_API_KEY no definida")
    exit(1)

client = genai.Client(api_key=api_key)

print(f"Contexto: {os.environ.get('AGENT_ARMY_CONTEXT')}")
print(f"Key prefix: {api_key[:10]}...\n")

print("=== Gemini 2.5 Flash (Marines) ===")
r = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Responde en una frase en español neutro: listo como tier Marines del SC17."
)
print(r.text + "\n")

print("=== Gemini 2.5 Flash-Lite (Logistics) ===")
r = client.models.generate_content(
    model="gemini-2.5-flash-lite",
    contents="Responde en una frase en español neutro: listo como tier Logistics del SC17."
)
print(r.text)
