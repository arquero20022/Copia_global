from odoo import models, fields

class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    def handle_barcode(self, barcode, event_id):
        # Lógica para manejar el código de barras
        attendee = self.env['calendar.attendee'].search([('barcode', '=', barcode)], limit=1)
        if attendee:
            return {"success": True, "attendee_id": attendee.id}
        else:
            return {"error": "Barcode not found"}
