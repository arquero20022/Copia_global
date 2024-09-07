class ThemeManager:
    def __init__(self, master):
        self.master = master

    def apply_theme(self, theme_name):
        """Apply a predefined theme to the report"""
        if theme_name == "Clásico":
            default_font_color = "black"
            default_background_color = "white"
        elif theme_name == "Moderno":
            default_font_color = "gray"
            default_background_color = "#f4f4f4"
        elif theme_name == "Minimalista":
            default_font_color = "black"
            default_background_color = "#ffffff"

        for row in range(self.master.grid_rows):
            for col in range(self.master.grid_cols):
                component = self.master.component_data.get((row, col))
                if component:
                    component['font_color'] = default_font_color
                    component['background_color'] = default_background_color
                    self.master.component_manager.update_component_visual(row, col)
