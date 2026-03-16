import requests
import os

def test_full_analysis():
    url = "http://localhost:8000/api/v1/analysis/process"
    test_pdfs_dir = r"c:\Users\USUARIO\Desktop\proyecto archivos nuevos\test_pdfs"
    
    # 1. Preparar metadatos
    data = {
        "institution_name": "I.E. Técnica Agroindustrial de Prueba",
        "tutor_name": "Antigravity AI Auditor"
    }
    
    # 2. Preparar archivos
    files = []
    file_handles = []
    try:
        supported_exts = (".pdf", ".txt", ".docx")
        for filename in os.listdir(test_pdfs_dir):
            if filename.lower().endswith(supported_exts):
                path = os.path.join(test_pdfs_dir, filename)
                # Abrir archivo y añadir a la lista de archivos para requests
                f = open(path, "rb")
                file_handles.append(f)
                
                # Determinar mimetype básico
                mime = "application/pdf"
                if filename.endswith(".txt"): mime = "text/plain"
                elif filename.endswith(".docx"): mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                
                files.append(("files", (filename, f, mime)))
        
        print(f"🚀 Iniciando testeo con {len(files)} archivos...")
        
        # 3. Realizar petición
        response = requests.post(url, data=data, files=files)
        
        # 4. Verificar resultado
        if response.status_code == 200:
            result = response.json()
            print("✅ TEST EXITOSO: El motor respondió correctamente.")
            print(f"📍 Institución: {result['institution_info']['name']}")
            print(f"📑 Categorías analizadas: {len(result['matrix'])}")
            print(f"📊 Pilares de calidad: {len(result['quality_report'])}")
            print(f"🔍 Estado de integridad: {result['integrity_check']['status']}")
            
            # Guardar el resultado real en un archivo para que el usuario lo vea
            import json
            output_path = r"c:\Users\USUARIO\Desktop\proyecto archivos nuevos\REAL_TEST_RESULT.json"
            with open(output_path, "w", encoding="utf-8") as f_out:
                json.dump(result, f_out, indent=2, ensure_ascii=False)
            print(f"📂 Resultado completo guardado en: {output_path}")
            
        else:
            print(f"❌ TEST FALLIDO: Código de estado {response.status_code}")
            print(f"Detalle: {response.text}")

    except Exception as e:
        print(f"💥 Error crítico durante el testeo: {str(e)}")
    finally:
        # Cerrar todos los archivos abiertos
        for f in file_handles:
            f.close()

if __name__ == "__main__":
    test_full_analysis()
