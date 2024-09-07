class OdooFieldManager:
    def __init__(self, master):
        self.master = master

    def add_dynamic_field(self, field_name):
        """Insert a dynamic Odoo t-field"""
        row, col = self.master.component_manager.get_selected_position()
        self.master.component_manager.place_component(row, col, f"<span t-field='{field_name}'/>", cols_to_span=1, font_size=12)

    def add_conditional_logic(self, condition):
        """Insert a t-if or t-foreach logic block"""
        row, col = self.master.component_manager.get_selected_position()
        self.master.component_manager.place_component(row, col, f"<t t-if='{condition}'>...</t>", cols_to_span=1, font_size=12)
