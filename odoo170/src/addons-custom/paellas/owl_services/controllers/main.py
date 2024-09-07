from odoo import http
from odoo.http import request

class BarcodeController(http.Controller):

    @http.route('/api/barcode/process', type='json', auth='user', methods=['POST'])
    def process_barcode(self, **post):
        barcode_data = post.get('barcode_data')
        if not barcode_data:
            return {'error': 'No barcode data provided'}

        # Solo procesa los datos del código de barras
        model = barcode_data.get('model')
        method = barcode_data.get('method')
        args = barcode_data.get('args')

        if not model or not method or not args:
            return {'error': 'Invalid data structure'}

        # Puedes realizar otras operaciones aquí, como registrar eventos, enviar notificaciones, etc.
        # Pero no se guardará nada en la base de datos.

        return {'status': 'Processed', 'data': barcode_data}


