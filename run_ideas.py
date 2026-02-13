import json
import os
import sys

# Add current directory to sys.path to ensure we can import local modules
sys.path.append(os.getcwd())

from generador_ideas import GeneradorIdeas

def main():
    try:
        # Define database path
        db_path = os.path.join(os.getcwd(), 'data', 'sistema.db')
        
        # Initialize generator
        generator = GeneradorIdeas(db_path)
        
        # Generate ideas
        # limit to 3 as per thought process, though user didn't specify quantity, 3 is a safe default for a quick task
        result = generator.generar_ideas(cantidad=3)
        
        # Print JSON to stdout
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        # Handle errors gracefully and print a JSON error object
        error_response = {
            "success": False,
            "error": str(e),
            "ideas": []
        }
        print(json.dumps(error_response, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
