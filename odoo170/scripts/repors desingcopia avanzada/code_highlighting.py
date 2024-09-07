from tkinter import simpledialog, colorchooser, tk


class ComponentManager:
    def __init__(self, master):
        self.master = master
        self.drag_data = {}
        self.component_id_counter = 0  # To generate unique component IDs

    def start_drag(self, event, component_type):
        """Iniciar el arrastre del componente"""
        cols_to_span = simpledialog.askinteger("Tamaño de columnas",
                                               f"¿Cuántas columnas debe ocupar {component_type}? (1-12)", minvalue=1,
                                               maxvalue=12)
        if cols_to_span is None:
            return  # Exit if the user cancels

        self.drag_data = {
            "component_type": component_type,
            "cols_to_span": cols_to_span,
            "widget": event.widget,
            "x": event.x,
            "y": event.y,
        }

        self.master.canvas.bind("<B1-Motion>", self.on_drag_motion)
        self.master.canvas.bind("<ButtonRelease-1>", self.on_drop)

    def on_drag_motion(self, event):
        """Handle visual dragging of the component on the canvas"""
        x, y = event.x, event.y
        self.master.canvas.delete("drag_preview")
        self.master.canvas.create_rectangle(
            x, y,
            x + self.drag_data["cols_to_span"] * self.master.cell_width, y + self.master.cell_height,
            outline="blue", tags="drag_preview"
        )

    def on_drop(self, event):
        """Handle dropping of the component into the grid"""
        x, y = event.x, event.y
        col = x // self.master.cell_width
        row = y // self.master.cell_height

        if col + self.drag_data["cols_to_span"] > self.master.grid_cols:
            return  # If the component doesn't fit, exit

        if not self.is_area_free(row, col, self.drag_data["cols_to_span"]):
            return  # Exit if the area is already occupied

        component_id = f"{self.drag_data['component_type']}_{self.component_id_counter}"
        self.component_id_counter += 1
        self.place_component(row, col, component_id)

        self.master.canvas.unbind("<B1-Motion>")
        self.master.canvas.unbind("<ButtonRelease-1>")
        self.master.canvas.delete("drag_preview")

    def is_area_free(self, row, col, cols_to_span):
        """Check if the area is free in the grid for placing the component."""
        for c in range(col, col + cols_to_span):
            if self.master.grid_components[row][c] is not None:
                return False
        return True

    def place_component(self, row, col, component_id):
        """Place the component visually in the grid and track its metadata"""
        cols_to_span = self.drag_data["cols_to_span"]
        x1 = col * self.master.cell_width
        y1 = row * self.master.cell_height
        x2 = x1 + cols_to_span * self.master.cell_width
        y2 = y1 + self.master.cell_height

        if self.drag_data["component_type"] in ["span", "h1", "h2"]:
            custom_text = simpledialog.askstring("Custom Text",
                                                 f"Enter the text for {self.drag_data['component_type']}:")
            if not custom_text:
                custom_text = "Texto de ejemplo"  # Default text
        else:
            custom_text = self.drag_data["component_type"].upper()

        if self.drag_data["component_type"] == "span_odoo":
            odoo_field = simpledialog.askstring("Odoo Field", "Enter Odoo field (e.g., o.name):")
            if odoo_field:
                display_text = f'<span t-field="{odoo_field}"/>'
        elif self.drag_data["component_type"] == "span_odoo_conditional":
            condition = simpledialog.askstring("Condition", "Enter the condition (e.g., o.is_active):")
            odoo_field = simpledialog.askstring("Odoo Field", "Enter Odoo field (e.g., o.name):")
            if condition and odoo_field:
                display_text = f'<span t-if="{condition}" t-field="{odoo_field}"/>'
        else:
            display_text = custom_text

        for c in range(col, col + cols_to_span):
            self.master.grid_components[row][c] = component_id

        canvas_id = self.master.canvas.create_rectangle(x1, y1, x2, y2, outline="black", fill="lightblue",
                                                        tags="component")
        text_id = self.master.canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=display_text, font=("Arial", 12),
                                                 tags="component")

        self.master.component_data[component_id] = {
            "component_type": self.drag_data["component_type"],
            "cols_to_span": cols_to_span,
            "font_size": 12,  # Default font size
            "font_color": "black",  # Default font color
            "background_color": "",  # No default background color
            "custom_text": custom_text,
            "row": row,
            "col": col,
            "canvas_id": canvas_id,
            "text_id": text_id,
            "odoo_field": odoo_field if "odoo" in self.drag_data["component_type"] else None,
            "condition": condition if "conditional" in self.drag_data["component_type"] else None,
        }

    def edit_background_color_by_id(self, component_id):
        """Edit the background color of the component by its ID."""
        component_data = self.master.component_data.get(component_id)
        if component_data:
            new_color = colorchooser.askcolor()[1]
            if new_color:
                component_data['background_color'] = new_color
                self.master.canvas.itemconfig(component_data['canvas_id'], fill=new_color)

    def edit_font_color_by_id(self, component_id):
        """Edit the font color of the component by its ID."""
        component_data = self.master.component_data.get(component_id)
        if component_data:
            new_color = colorchooser.askcolor()[1]
            if new_color:
                component_data['font_color'] = new_color
                self.master.canvas.itemconfig(component_data['text_id'], fill=new_color)

    def edit_font_size_by_id(self, component_id):
        """Edit the font size of the component by its ID."""
        component_data = self.master.component_data.get(component_id)
        if component_data:
            new_font_size = simpledialog.askinteger("Edit Font Size", "Enter new font size:",
                                                    initialvalue=component_data["font_size"], minvalue=8, maxvalue=32)
            if new_font_size:
                component_data['font_size'] = new_font_size
                self.master.canvas.itemconfig(component_data['text_id'], font=("Arial", new_font_size))

    def edit_text_by_id(self, component_id):
        """Edit the text or field of the component based on its type."""
        component_data = self.master.component_data.get(component_id)
        if not component_data:
            return

        if component_data["component_type"] in ["span", "h1", "h2"]:
            new_text = simpledialog.askstring("Edit Text", "Enter new text:",
                                              initialvalue=component_data["custom_text"])
            if new_text:
                component_data["custom_text"] = new_text
                self.master.canvas.itemconfig(component_data['text_id'], text=new_text)

        elif component_data["component_type"] == "span_odoo":
            new_field = simpledialog.askstring("Edit Odoo Field", "Enter new Odoo field (e.g., o.name):",
                                               initialvalue=component_data.get("odoo_field"))
            if new_field:
                component_data["odoo_field"] = new_field
                self.master.canvas.itemconfig(component_data['text_id'], text=f'<span t-field="{new_field}"/>')

        elif component_data["component_type"] == "span_odoo_conditional":
            new_condition = simpledialog.askstring("Edit Condition", "Enter new condition:",
                                                   initialvalue=component_data.get("condition"))
            new_field = simpledialog.askstring("Edit Odoo Field", "Enter new Odoo field (e.g., o.name):",
                                               initialvalue=component_data.get("odoo_field"))
            if new_condition and new_field:
                component_data["condition"] = new_condition
                component_data["odoo_field"] = new_field
                self.master.canvas.itemconfig(component_data['text_id'],
                                              text=f'<span t-if="{new_condition}" t-field="{new_field}"/>')

    def delete_component_by_id(self, component_id):
        """Delete the selected component from the canvas and grid."""
        component_data = self.master.component_data.pop(component_id, None)
        if component_data:
            row = component_data['row']
            col = component_data['col']
            for c in range(col, col + component_data['cols_to_span']):
                self.master.grid_components[row][c] = None

            self.master.canvas.delete(component_data['canvas_id'])  # Remove rectangle
            self.master.canvas.delete(component_data['text_id'])  # Remove text

    def generate_html(self):
        """Generates HTML code based on the components placed in the grid."""
        html_code = []
        used_ids = set()

        def add_indented_line(line, level):
            indent = '    ' * level  # Use 4 spaces for each indentation level
            html_code.append(f"{indent}{line.strip()}")  # Clean up any extra spaces

        indent_level = 0
        add_indented_line('<template id="custom_report_template" name="Custom Report Template">', indent_level)
        indent_level += 1
        add_indented_line('<t t-name="custom_report_template">', indent_level)
        indent_level += 1
        add_indented_line('<t t-call="web.external_layout">', indent_level)
        indent_level += 1

        last_filled_row = 0
        for row in range(self.master.grid_rows):
            if any(self.master.grid_components[row][col] is not None for col in range(self.master.grid_cols)):
                last_filled_row = row

        row = 0
        while row <= last_filled_row:
            current_col = 0
            if all(self.master.grid_components[row][col] is None for col in range(self.master.grid_cols)):
                empty_row_count = 1
                for next_row in range(row + 1, last_filled_row + 1):
                    if all(self.master.grid_components[next_row][col] is None for col in range(self.master.grid_cols)):
                        empty_row_count += 1
                    else:
                        break
                add_indented_line(f'<div class="row" style="height: {empty_row_count * 10}px;">', indent_level)
                indent_level += 1
                add_indented_line(f'<!-- Fila vacía, combinando {empty_row_count} filas -->', indent_level)
                indent_level -= 1
                add_indented_line('</div>', indent_level)
                row += empty_row_count
            else:
                add_indented_line('<div class="row" style="height: 10px;">', indent_level)
                indent_level += 1
                while current_col < self.master.grid_cols:
                    component_id = self.master.grid_components[row][current_col]

                    if component_id is not None and component_id not in used_ids:
                        component_data = self.master.component_data.get(component_id)
                        if component_data:
                            cols_to_span = component_data["cols_to_span"]
                            font_size = component_data["font_size"]
                            font_color = component_data["font_color"]
                            background_color = component_data["background_color"]
                            custom_text = component_data["custom_text"]

                            if component_data["component_type"] == "h1":
                                add_indented_line(
                                    f'<div class="col-{cols_to_span}"><h1 style="font-size: {font_size}px; color: {font_color}; background-color: {background_color};">{custom_text}</h1></div>',
                                    indent_level)

                            elif component_data["component_type"] == "h2":
                                add_indented_line(
                                    f'<div class="col-{cols_to_span}"><h2 style="font-size: {font_size}px; color: {font_color}; background-color: {background_color};">{custom_text}</h2></div>',
                                    indent_level)

                            elif component_data["component_type"] == "span":
                                add_indented_line(
                                    f'<div class="col-{cols_to_span}"><span style="font-size: {font_size}px; color: {font_color}; background-color: {background_color};">{custom_text}</span></div>',
                                    indent_level)

                            elif component_data["component_type"] == "span_odoo":
                                odoo_field = component_data["odoo_field"]
                                add_indented_line(
                                    f'<div class="col-{cols_to_span}"><span t-field="{odoo_field}"/></div>',
                                    indent_level)

                            elif component_data["component_type"] == "span_odoo_conditional":
                                odoo_field = component_data["odoo_field"]
                                condition = component_data["condition"]
                                add_indented_line(
                                    f'<div class="col-{cols_to_span}"><span t-if="{condition}" t-field="{odoo_field}"/></div>',
                                    indent_level)

                            elif component_data["component_type"] == "table":
                                add_indented_line(f'<div class="col-{cols_to_span}">', indent_level)
                                indent_level += 1
                                add_indented_line('<table class="table">', indent_level)
                                indent_level += 1
                                add_indented_line('<thead><tr><th>Header 1</th><th>Header 2</th></tr></thead>',
                                                  indent_level)
                                add_indented_line('<tbody><tr><td>Dato 1</td><td>Dato 2</td></tr></tbody>',
                                                  indent_level)
                                indent_level -= 1
                                add_indented_line('</table>', indent_level)
                                indent_level -= 1
                                add_indented_line('</div>', indent_level)

                            used_ids.add(component_id)
                        current_col += cols_to_span
                    else:
                        empty_col_count = 1
                        for next_col in range(current_col + 1, self.master.grid_cols):
                            if self.master.grid_components[row][next_col] is None:
                                empty_col_count += 1
                            else:
                                break
                        add_indented_line(f'<div class="col-{empty_col_count}"></div>', indent_level)
                        current_col += empty_col_count

                indent_level -= 1
                add_indented_line('</div>', indent_level)
                row += 1

        indent_level -= 1
        add_indented_line('</t>', indent_level)
        indent_level -= 1
        add_indented_line('</t>', indent_level)
        indent_level -= 1
        add_indented_line('</template>', indent_level)

        return "\n".join(html_code)

    def highlight_pattern(self, pattern, color, start="1.0", end="end"):
        """Apply the color to the text that matches the pattern."""
        start_pos = self.master.code_output.index(start)
        while True:
            match = self.master.code_output.search(pattern, start_pos, stopindex=end, regexp=True)
            if not match:
                break
            end_pos = f"{match}+{len(self.master.code_output.get(match, f'{match} lineend'))}c"
            self.master.code_output.tag_add(pattern, match, end_pos)
            self.master.code_output.tag_config(pattern, foreground=color)
            start_pos = end_pos

    def display_code_with_highlighting(self, html_code):
        """Display the HTML code with syntax highlighting."""
        self.master.code_output.delete(1.0, tk.END)

        # Define colors for syntax highlighting
        tag_color = "#008080"  # Teal for tags
        attribute_color = "#0000FF"  # Blue for attributes
        value_color = "#800080"  # Purple for values
        comment_color = "#808080"  # Gray for comments

        # Insert the code into the widget without any formatting first
        self.master.code_output.insert(tk.END, html_code)

        # Highlight HTML tags
        self.highlight_pattern(r"</?[\w\-]+", tag_color)  # Matches HTML opening/closing tags
        self.highlight_pattern(r"<[\w\-]+", tag_color)  # Matches tag names
        self.highlight_pattern(r"</[\w\-]+>", tag_color)  # Matches closing tags

        # Highlight HTML attributes
        self.highlight_pattern(r'\b[\w\-]+=', attribute_color)  # Matches attributes like "class="

        # Highlight attribute values (inside quotes)
        self.highlight_pattern(r'"[^"]*"', value_color)  # Matches values inside double quotes

        # Highlight HTML comments
        self.highlight_pattern(r'<!--.*?-->', comment_color)  # Matches comments like <!-- comment -->
