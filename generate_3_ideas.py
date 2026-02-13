from generador_ideas import GeneradorIdeas
import os
import json

def main():
    db_path = os.path.join('data', 'sistema.db')
    generador = GeneradorIdeas(db_path)
    resultado = generador.generar_ideas(cantidad=3)
    
    if resultado['success']:
        print(json.dumps(resultado['ideas'], indent=2, ensure_ascii=False))
    else:
        print(f"Error: {resultado['error']}")

if __name__ == "__main__":
    main()
