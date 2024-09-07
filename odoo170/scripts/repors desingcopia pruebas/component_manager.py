from tkinter import simpledialog, colorchooser
import tkinter as tk


class ComponentManager:
    def __init__(self, master):
        self.master = master
        self.drag_data = {}
        self.component_id_counter = 0  # To generate unique component IDs
        self.moving_component_id = None  # Track if a component is being moved

    def start_drag(self, event, component_type=None):
        """Iniciar el arrastre del componente, o mover uno existente."""
        col = event.x // self.master.cell_width
        row = event.y // self.master.cell_height

        existing_component_id = self.master.grid_components[row][col]

        # If clicking on an existing component, allow movement
        if existing_component_id:
            component_data = self.master.component_data[existing_component_id]
            self.moving_component_id = existing_component_id
            self.drag_data = {
                "component_type": component_data['component_type'],
                "cols_to_span": component_data['cols_to_span'],
                "widget": event.widget,
                "x": event.x,
                "y": event.y,
                "row": component_data["row"],
                "col": component_data["col"],
            }

            self.master.canvas.bind("<B1-Motion>", self.on_drag_motion)
            self.master.canvas.bind("<ButtonRelease-1>", self.on_drop_movement)
        elif component_type:
            # Proceed with normal dragging if not an existing component
            cols_to_span = simpledialog.askinteger("Tamaño de columnas",
                                                   f"¿Cuántas columnas debe ocupar {component_type}? (1-12)",
                                                   minvalue=1, maxvalue=12)
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

    def on_drop_movement(self, event):
        """Handle dropping the component to move it to a new location."""
        x, y = event.x, event.y
        col = x // self.master.cell_width
        row = y // self.master.cell_height

        if col + self.drag_data["cols_to_span"] > self.master.grid_cols:
            return  # Exit if the component doesn't fit

        if not self.is_area_free(row, col, self.drag_data["cols_to_span"]):
            return  # Exit if the area is already occupied

        self.move_component(row, col, self.moving_component_id)

        self.master.canvas.unbind("<B1-Motion>")
        self.master.canvas.unbind("<ButtonRelease-1>")
        self.master.canvas.delete("drag_preview")
        self.moving_component_id = None

    def move_component(self, row, col, component_id):
        """Move the existing component to a new location."""
        component_data = self.master.component_data[component_id]

        # Clear previous position
        prev_row, prev_col = component_data['row'], component_data['col']
        for c in range(prev_col, prev_col + component_data['cols_to_span']):
            self.master.grid_components[prev_row][c] = None

        # Update new position
        for c in range(col, col + component_data['cols_to_span']):
            self.master.grid_components[row][c] = component_id

        # Move the component visually
        x1 = col * self.master.cell_width
        y1 = row * self.master.cell_height
        x2 = x1 + component_data['cols_to_span'] * self.master.cell_width
        y2 = y1 + self.master.cell_height

        self.master.canvas.coords(component_data['canvas_id'], x1, y1, x2, y2)
        self.master.canvas.coords(component_data['text_id'], (x1 + x2) / 2, (y1 + y2) / 2)

        # Update component data
        component_data['row'] = row
        component_data['col'] = col

    def add_css_styling(self, component_id):
        """Add CSS styling options like margins, padding, and custom class."""
        component_data = self.master.component_data.get(component_id)
        if component_data:
            new_margin = simpledialog.askstring("Edit Margin", "Enter margin (e.g., 10px):")
            new_padding = simpledialog.askstring("Edit Padding", "Enter padding (e.g., 5px):")
            new_class = simpledialog.askstring("Edit CSS Class", "Enter CSS class:")

            if new_margin:
                component_data['margin'] = new_margin
            if new_padding:
                component_data['padding'] = new_padding
            if new_class:
                component_data['class'] = new_class

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
                            margin = component_data.get("margin", "")
                            padding = component_data.get("padding", "")
                            css_class = component_data.get("class", "")

                            # Build the style string
                            style_attributes = []
                            if margin:
                                style_attributes.append(f"margin: {margin};")
                            if padding:
                                style_attributes.append(f"padding: {padding};")
                            if background_color:
                                style_attributes.append(f"background-color: {background_color};")
                            if font_size:
                                style_attributes.append(f"font-size: {font_size}px;")
                            if font_color:
                                style_attributes.append(f"color: {font_color};")

                            style_str = " ".join(style_attributes)
                            class_str = f'class="{css_class}"' if css_class else ""

                            if component_data["component_type"] == "span_odoo":
                                odoo_field = component_data["odoo_field"]
                                add_indented_line(f'<div class="col-{cols_to_span}">', indent_level)
                                indent_level += 1
                                add_indented_line(
                                    f'<span t-field="{odoo_field}" {class_str} style="{style_str}"></span>',
                                    indent_level)
                                indent_level -= 1
                                add_indented_line('</div>', indent_level)

                            elif component_data["component_type"] == "span_odoo_conditional":
                                odoo_field = component_data["odoo_field"]
                                condition = component_data["condition"]
                                add_indented_line(f'<div class="col-{cols_to_span}">', indent_level)
                                indent_level += 1
                                add_indented_line(
                                    f'<span t-if="{condition}" t-field="{odoo_field}" {class_str} style="{style_str}"></span>',
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

