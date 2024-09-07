import base64
import xlrd
import requests
from odoo import api, models



class ResCompany(models.Model):
    _inherit = 'res.company'

    def process_excel_file(self):
        # Ruta del archivo Excel
        excel_path = '/opt/sources/odoo170/image.xlsx'

        # Abre el archivo Excel
        try:
            print(f"Abriendo el archivo Excel: {excel_path}")
            wb = xlrd.open_workbook(excel_path)
            sheet = wb.sheet_by_index(0)
            print(f"El archivo tiene {sheet.nrows} filas.")
        except Exception as e:
            print(f"Error al abrir el archivo Excel: {e}")
            return

        # Itera sobre las filas del archivo Excel
        for row in range(1, sheet.nrows):  # Saltamos la primera fila (encabezados)
            name = sheet.cell_value(row, 0)
            image_url = sheet.cell_value(row, 1)
            product_ref = sheet.cell_value(row, 2)


            # Validar que el product_ref no sea un float



            # Buscar el producto basado en el campo external_id (o cualquier otro campo que quieras usar como referencia)

            product_template = self.env.ref(product_ref)


           # if not product_template:
            #    print(f"No se encontró el producto con referencia externa {product_ref} en la fila {row}")
             #   continue

            # Convertir la imagen URL en base64
            try:
                print(f"Descargando imagen desde {image_url}...")
                image_data = base64.b64encode(requests.get(image_url).content)
                print(f"Imagen descargada y convertida a base64.")
            except Exception as e:
                print(f"Error al descargar la imagen para la fila {row}: {e}")
                continue

            # Crear el registro en el modelo 'product.image'
            try:

                self.env['product.image'].create({
                    'name': name,
                    'image_1920': image_data,  # Campo de imagen
                    'product_tmpl_id': product_template.id,


                })
                print(f"Imagen creada para el producto {name}.")
            except Exception as e:
                print(f"Error al crear la imagen en la fila {row}: {e}")
