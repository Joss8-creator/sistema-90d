import logging
import sys
from gemini_integration import GeminiCLI

# Configure logging to see debug output
logging.basicConfig(level=logging.DEBUG)

def test_generation():
    print("Testing Gemini CLI generation...")
    gemini = GeminiCLI()
    
    prompt = "Retorna un JSON con {'mensaje': 'Hola mundo'}"
    
    print(f"Executing prompt: {prompt}")
    resultado = gemini.ejecutar_con_json(prompt)
    
    print("\n--- Resultado ---")
    print(f"Success: {resultado['success']}")
    if resultado['success']:
        print(f"Respuesta parseada: {resultado.get('json')}")
    else:
        print(f"Error: {resultado['error']}")
        print(f"Stderr: {resultado.get('stderr')}")

if __name__ == "__main__":
    test_generation()
