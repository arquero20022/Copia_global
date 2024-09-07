import xlrd
import base64
import xmlrpc.client
import requests  # Necesario para hacer la descarga de la imagen

# Datos de conexión
url = 'https://catriocabo.ingenieriacloud.com/'
db = 'catriocabo'
username = 'serin'
password = 'ic2015$x'

# Conexión con Odoo
print("Conectando con Odoo...")
common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})

print(f"Autenticado con UID: {uid}")

models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

# Abrir el archivo Excel
archivo_excel = 'image.xlsx'
print(f"Abriendo el archivo Excel: {archivo_excel}")
wb = xlrd.open_workbook(archivo_excel)
sheet = wb.sheet_by_index(0)

print(f"El archivo tiene {sheet.nrows} filas.")

# Iterar sobre las filas del archivo
for row in range(1, sheet.nrows):  # Saltamos la primera fila (encabezados)
    name = sheet.cell_value(row, 0)
    image_url = sheet.cell_value(row, 1)
    product_ref = sheet.cell_value(row, 2)  # Cambiado el nombre a product_ref
    external_id = sheet.cell_value(row, 3)

    print(f"Procesando fila {row}: name={name}, image_url={image_url}, product_ref={product_ref}, external_id={external_id}")

    # Buscar el ID real de 'product_tmpl_id' usando la referencia externa
    try:
        print(f"Buscando el ID para el producto con referencia: {product_ref}")

        # Usamos 'search' en lugar de 'search_read' para buscar el producto primero
        product_ids = models.execute_kw(db, uid, password, 'product.template', 'search',
                                        [[('default_code', '=', product_ref)]])  # Reemplaza 'default_code' si es necesario

        if not product_ids:
            print(f"No se encontró un producto con la referencia {product_ref} en la fila {row}. Saltando...")
            continue

        # Ahora usamos 'read' para obtener los detalles del producto
        product_template = models.execute_kw(db, uid, password, 'product.template', 'read', [product_ids], {'fields': ['id']})
        product_tmpl_id = product_template[0]['id']
        print(f"ID del producto encontrado: {product_tmpl_id}")
    except Exception as e:
        print(f"Error al buscar el producto para la fila {row}: {e}")
        continue

    # Convertir la imagen URL en base64
    try:
        print(f"Descargando imagen desde {image_url}...")
        image_data = xmlrpc.client.Binary(base64.b64encode(requests.get(image_url).content))
        print(f"Imagen descargada y convertida a base64.")
    except Exception as e:
        print(f"Error al descargar la imagen para la fila {row}: {e}")
        continue

    # Crear el registro en el modelo 'product.image'
    try:
        print(f"Creando registro de imagen en Odoo para el producto con ID: {product_tmpl_id}...")
        record_id = models.execute_kw(db, uid, password, 'product.image', 'create', [{
            'name': name,
            'image_1920': image_data,  # Asegúrate de que este es el campo correcto para la imagen
            'product_tmpl_id': product_tmpl_id,
            'id': external_id  # Asumiendo que 'x_external_id' es el campo para el external_id
        }])
        print(f"Imagen creada con ID: {record_id}")
    except Exception as e:
        print(f"Error al crear la imagen en la fila {row}: {e}")
