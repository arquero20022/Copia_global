from tkinter import simpledialog, colorchooser
import tkinter as tk


class ComponentManager:
    def __init__(self, master):
        self.master = master
        self.drag_data = {}
        self.component_id_counter = 0  # To generate unique component IDs

    def start_drag(self, event, component_type):
        """Iniciar el arrastre del componente"""
        cols_to_span = simpledialog.askinteger("Tamaño de columnas", f"¿Cuántas columnas debe ocupar {component_type}? (1-12)", minvalue=1, maxvalue=12)
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

        # Default value for custom_text to avoid UnboundLocalError
        custom_text = ""

        # Handle different component types
        if self.drag_data["component_type"] in ["span", "h1", "h2"]:
            custom_text = simpledialog.askstring("Custom Text",
                                                 f"Enter the text for {self.drag_data['component_type']}:")
            if not custom_text:
                custom_text = "Texto de ejemplo"  # Default text if user cancels
        elif self.drag_data["component_type"] == "table":
            # Ask the user for the number of columns
            num_columns = simpledialog.askinteger("Number of Columns", "Enter the number of columns for the table:",
                                                  minvalue=1, initialvalue=2)
            if num_columns is None:
                return  # If the user cancels, do not place the component
            component_id = f"table_{self.component_id_counter}"
            display_text = "Table"
        elif self.drag_data["component_type"] == "span_odoo":
            odoo_field = simpledialog.askstring("Odoo Field", "Enter Odoo field (e.g., o.name):")
            if odoo_field:
                component_id = f"span_odoo_{self.component_id_counter}"
                display_text = f'<span t-field="{odoo_field}"/>'
        elif self.drag_data["component_type"] == "span_odoo_conditional":
            condition = simpledialog.askstring("Condition", "Enter the condition (e.g., o.is_active):")
            odoo_field = simpledialog.askstring("Odoo Field", "Enter Odoo field (e.g., o.name):")
            if condition and odoo_field:
                component_id = f"span_condicional_{self.component_id_counter}"
                display_text = f'<span t-if="{condition}" t-field="{odoo_field}"/>'
        else:
            # If none of the above types, use the uppercased component type as the default text
            custom_text = self.drag_data["component_type"].upper()
            display_text = custom_text

        # Continue placing the component on the grid and canvas
        for c in range(col, col + cols_to_span):
            self.master.grid_components[row][c] = component_id

        canvas_id = self.master.canvas.create_rectangle(x1, y1, x2, y2, outline="black", fill="lightblue",
                                                        tags="component")
        text_id = self.master.canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=display_text, font=("Arial", 12),
                                                 tags="component")

        # Save the component data, including num_columns for tables
        self.master.component_data[component_id] = {
            "component_type": self.drag_data["component_type"],
            "cols_to_span": cols_to_span,
            "font_size": 12,
            "font_color": "black",
            "background_color": "",
            "custom_text": custom_text if self.drag_data["component_type"] not in ["table"] else None,
            "row": row,
            "col": col,
            "canvas_id": canvas_id,
            "text_id": text_id,
            "odoo_field": odoo_field if "odoo" in self.drag_data["component_type"] else None,
            "condition": condition if "conditional" in self.drag_data["component_type"] else None,
            "num_columns": num_columns if self.drag_data["component_type"] == "table" else None
        }

        self.component_id_counter += 1

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
            new_font_size = simpledialog.askinteger("Edit Font Size", "Enter new font size:", initialvalue=component_data["font_size"], minvalue=8, maxvalue=32)
            if new_font_size:
                component_data['font_size'] = new_font_size
                self.master.canvas.itemconfig(component_data['text_id'], font=("Arial", new_font_size))

    def edit_odoo_field_by_id(self, component_id):
        """Edit only the Odoo field of the component by its ID."""
        component_data = self.master.component_data.get(component_id)
        if component_data and component_data["component_type"] in ["span_odoo", "span_odoo_conditional"]:
            new_field = simpledialog.askstring("Edit Odoo Field", "Enter new Odoo field (e.g., o.name):",
                                               initialvalue=component_data.get("odoo_field"))
            if new_field:
                component_data["odoo_field"] = new_field
                if component_data["component_type"] == "span_odoo":
                    self.master.canvas.itemconfig(component_data['text_id'], text=f'<field="{new_field}"/>')
                elif component_data["component_type"] == "span_odoo_conditional":
                    condition = component_data.get("condition", "")
                    self.master.canvas.itemconfig(component_data['text_id'],
                                                  text=f'<if="{condition}"field="{new_field}"/>')

    def edit_table_columns_by_id(self, component_id):
        """Edit the number of columns in a table component."""
        component_data = self.master.component_data.get(component_id)
        if component_data and component_data["component_type"] == "table":
            new_num_columns = simpledialog.askinteger("Edit Table Columns", "Enter new number of columns:",
                                                      initialvalue=component_data["num_columns"], minvalue=1,
                                                      maxvalue=10)
            if new_num_columns:
                component_data["num_columns"] = new_num_columns
                display_text = f"<table><thead><tr>{''.join(['<th>Header</th>' for _ in range(new_num_columns)])}</tr></thead><tbody><tr>{''.join(['<td>Data</td>' for _ in range(new_num_columns)])}</tr></tbody></table>"
                self.master.canvas.itemconfig(component_data['text_id'], text=display_text)

    def edit_condition_by_id(self, component_id):
        """Edit only the condition (t-if) of the component by its ID."""
        component_data = self.master.component_data.get(component_id)
        if component_data and component_data["component_type"] == "span_odoo_conditional":
            new_condition = simpledialog.askstring("Edit Condition", "Enter new condition:",
                                                   initialvalue=component_data.get("condition"))
            if new_condition:
                component_data["condition"] = new_condition
                odoo_field = component_data.get("odoo_field", "")
                self.master.canvas.itemconfig(component_data['text_id'],
                                              text=f'<if="{new_condition}" field="{odoo_field}"/>')

    def edit_text_by_id(self, component_id):
        """Edit the text or field of the component based on its type."""
        component_data = self.master.component_data.get(component_id)
        if not component_data:
            return

        if component_data["component_type"] in ["span", "h1", "h2"]:
            new_text = simpledialog.askstring("Edit Text", "Enter new text:", initialvalue=component_data["custom_text"])
            if new_text:
                component_data["custom_text"] = new_text
                self.master.canvas.itemconfig(component_data['text_id'], text=new_text)

        elif component_data["component_type"] == "span_odoo":
            new_field = simpledialog.askstring("Edit Odoo Field", "Enter new Odoo field (e.g., o.name):", initialvalue=component_data.get("odoo_field"))
            if new_field:
                component_data["odoo_field"] = new_field
                self.master.canvas.itemconfig(component_data['text_id'], text=f'<span t-field="{new_field}"/>')

        elif component_data["component_type"] == "span_odoo_conditional":
            new_condition = simpledialog.askstring("Edit Condition", "Enter new condition:", initialvalue=component_data.get("condition"))
            new_field = simpledialog.askstring("Edit Odoo Field", "Enter new Odoo field (e.g., o.name):", initialvalue=component_data.get("odoo_field"))
            if new_condition and new_field:
                component_data["condition"] = new_condition
                component_data["odoo_field"] = new_field
                self.master.canvas.itemconfig(component_data['text_id'], text=f'<if="{new_condition}" field="{new_field}"/>')

    def delete_component_by_id(self, component_id):
        """Delete the selected component from the canvas and grid."""
        component_data = self.master.component_data.pop(component_id, None)
        if component_data:
            row = component_data['row']
            col = component_data['col']
            for c in range(col, col + component_data['cols_to_span']):
                self.master.grid_components[row][c] = None

            self.master.canvas.delete(component_data['canvas_id'])  # Remove rectangle
            self.master.canvas.delete(component_data['text_id'])    # Remove text

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

    def generate_html(self):
        """Generates HTML code based on the components placed in the grid."""
        html_code = []
        used_ids = set()

        def add_indented_line(line, level):
            indent = '    ' * level  # Use 4 spaces for each indentation level
            html_code.append(f"{indent}{line.strip()}")

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

                            if component_data["component_type"] == "span_odoo":
                                odoo_field = component_data["odoo_field"]
                                add_indented_line(f'<div class="col-{cols_to_span}">', indent_level)
                                indent_level += 1
                                add_indented_line(
                                    f'<span t-field="{odoo_field}" style="font-size: {font_size}px; color: {font_color}; background-color: {background_color};"></span>',
                                    indent_level)
                                indent_level -= 1
                                add_indented_line('</div>', indent_level)

                            elif component_data["component_type"] == "span_odoo_conditional":
                                odoo_field = component_data["odoo_field"]
                                condition = component_data["condition"]
                                add_indented_line(f'<div class="col-{cols_to_span}">', indent_level)
                                indent_level += 1
                                add_indented_line(
                                    f'<span t-if="{condition}" t-field="{odoo_field}" style="font-size: {font_size}px; color: {font_color}; background-color: {background_color};"></span>',
                                    indent_level)
                                indent_level -= 1
                                add_indented_line('</div>', indent_level)

                            elif component_data["component_type"] == "table":
                                # Get the number of columns for the table
                                num_columns = component_data.get("num_columns", 1)  # Default to 1 if not set

                                add_indented_line(f'<div class="col-{cols_to_span}">', indent_level)
                                indent_level += 1
                                add_indented_line('<table class="table">', indent_level)
                                indent_level += 1

                                # Add the table headers
                                add_indented_line('<thead>', indent_level)
                                indent_level += 1
                                add_indented_line('<tr>', indent_level)
                                indent_level += 1
                                for i in range(num_columns):
                                    add_indented_line(f'<th>Header {i + 1}</th>', indent_level)
                                indent_level -= 1
                                add_indented_line('</tr>', indent_level)
                                indent_level -= 1
                                add_indented_line('</thead>', indent_level)

                                # Add the table body
                                add_indented_line('<tbody>', indent_level)
                                indent_level += 1
                                add_indented_line('<tr>', indent_level)
                                indent_level += 1
                                for i in range(num_columns):
                                    add_indented_line(f'<td>Data {i + 1}</td>', indent_level)
                                indent_level -= 1
                                add_indented_line('</tr>', indent_level)
                                indent_level -= 1
                                add_indented_line('</tbody>', indent_level)

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







