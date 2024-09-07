import requests

# Ruta al archivo de texto que contiene el código ZPL
source_file = 'source.txt'

# Leer el contenido del archivo ZPL
with open(source_file, 'r') as file:
    zpl_data = file.read()

# Configurar los parámetros para la solicitud a la API de Labelary
url = 'http://api.labelary.com/v1/printers/8dpmm/labels/4x6/0/'  # Ajustar el tamaño según sea necesario
files = {'file': zpl_data}  # Enviar el contenido ZPL como parte de los archivos
headers = {'Accept': 'application/pdf'}  # Para recibir un PDF

# Hacer la solicitud POST a la API con multipart/form-data
response = requests.post(url, headers=headers, files=files, stream=True)

# Verificar si la solicitud fue exitosa
if response.status_code == 200:
    # Guardar el PDF resultante en un archivo
    with open('label.pdf', 'wb') as output_file:
        output_file.write(response.content)
    print("El archivo PDF se ha generado exitosamente como 'label.pdf'.")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
