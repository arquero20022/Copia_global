from odoo import models, fields

class CustomBarcodeModel(models.Model):
    _name = 'custom.barcode.model'
    _description = 'Custom Barcode Model'

    barcode_value = fields.Char(string="Barcode Value")

    # Campo Many2one que apunta a calendar.event filtrado por el campo name igual al barcode_value
    related_event_id = fields.Many2one(
        'calendar.event',
        string='Evento Relacionado',
        domain="[('name', '=', barcode_value)]"
    )

    def print_barcode_value(self):
        print("dentro")
        """Imprime el valor del código de barras en la consola del servidor."""
        for record in self:
            print(f"Barcode Value: {record.barcode_value}")
