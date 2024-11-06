import tkinter as tk
import openai
import re

openai.api_key = "replace api keys here"



class RoomLayoutApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI-Generated Editable Room Layout")
        self.root.geometry("600x800")

        # Room dimension input fields
        self.width_label = tk.Label(root, text="Room Width (in feet):")
        self.width_label.pack()
        self.width_entry = tk.Entry(root)
        self.width_entry.pack()

        self.height_label = tk.Label(root, text="Room Height (in feet):")
        self.height_label.pack()
        self.height_entry = tk.Entry(root)
        self.height_entry.pack()

        # Dropdown to select room type
        self.room_type_label = tk.Label(root, text="Select Room Type:")
        self.room_type_label.pack()
        self.room_type = tk.StringVar(root)
        self.room_type.set("Living Room")
        self.room_type_dropdown = tk.OptionMenu(root, self.room_type, "Living Room", "Bedroom", "Kitchen", "Bathroom")
        self.room_type_dropdown.pack()

        # Button to generate layout
        self.generate_button = tk.Button(root, text="Generate Blueprint", command=self.generate_layout)
        self.generate_button.pack(pady=10)

        # Canvas to display the blueprint
        self.canvas = tk.Canvas(root, width=512, height=512, bg="white")
        self.canvas.pack(pady=20)

        # Text entry for edit commands
        self.command_label = tk.Label(root, text="Enter Edit Command:")
        self.command_label.pack()
        self.command_entry = tk.Entry(root, width=50)
        self.command_entry.pack()
        self.command_button = tk.Button(root, text="Apply Edit", command=self.apply_edit)
        self.command_button.pack(pady=10)

        # Placeholder for layout data
        self.layout_data = []

    def generate_layout(self):
        # Create prompt for OpenAI
        room_type = self.room_type.get()
        width = self.width_entry.get()
        height = self.height_entry.get()
        prompt = (
            f"Generate a detailed blueprint for a single-story {room_type} with a width of {width} feet and a height of {height} feet. "
            f"Include elements like walls, doors, and typical furniture (e.g., bed, sofa, table, window) with specific positions and dimensions. "
            f"Output the response in the following format strictly:\n"
            f"Item: [Type]\nCoordinates (x, y): ([value], [value])\nDimensions (width, height): [value] x [value]\n"
            f"All dimensions should be in feet, and the (0, 0) point should be the bottom-left corner of the room."
        )

        response = self.generate_text(prompt)
        if response:
            layout_data = self.parse_layout(response)
            if layout_data:
                self.layout_data = layout_data
                self.display_layout()
            else:
                print("Failed to parse layout.")
        else:
            print("Failed to generate layout.")

    def generate_text(self, prompt):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000  # Increased to ensure full response is captured
            )
            text_response = response['choices'][0]['message']['content'].strip()
            print("API Response:", text_response)  # Debugging print to see the full response
            return text_response
        except Exception as e:
            print(f"Error generating text: {e}")
            return None

    def parse_layout(self, response_text):
        layout_data = []
        item_pattern = r"Item: (\w+)"
        coordinates_pattern = r"Coordinates \(x, y\): \((\d+), (\d+)\)"
        dimensions_pattern = r"Dimensions \(width, height\): (\d+) x (\d+)"

        lines = response_text.split('\n')
        current_item, x, y, width, height = None, None, None, None, None

        for line in lines:
            # Extract item type
            item_match = re.search(item_pattern, line)
            if item_match:
                current_item = item_match.group(1)

            # Extract coordinates
            coordinates_match = re.search(coordinates_pattern, line)
            if coordinates_match:
                x, y = map(int, coordinates_match.groups())

            # Extract dimensions
            dimensions_match = re.search(dimensions_pattern, line)
            if dimensions_match:
                width, height = map(int, dimensions_match.groups())

                # Add the extracted data to layout_data if complete
                if current_item and x is not None and y is not None and width is not None and height is not None:
                    layout_data.append({
                        'type': current_item,
                        'x': x,
                        'y': y,
                        'width': width,
                        'height': height
                    })
                    # Reset the temporary variables for next item
                    current_item, x, y, width, height = None, None, None, None, None

        # Debug: Check if any layout data was parsed
        if len(layout_data) == 0:
            print("No valid items parsed from response. Response text was:")
            print(response_text)

        return layout_data

    def display_layout(self):
        # Clear the canvas
        self.canvas.delete("all")
        room_width = int(self.width_entry.get())
        room_height = int(self.height_entry.get())
        canvas_width, canvas_height = 512, 512
        x_scale = canvas_width / room_width
        y_scale = canvas_height / room_height

        # Draw room boundaries
        self.canvas.create_rectangle(10, 10, canvas_width - 10, canvas_height - 10, outline="black", width=3)

        # Draw each furniture item based on parsed layout data
        for item in self.layout_data:
            x = item['x'] * x_scale + 10
            y = item['y'] * y_scale + 10
            width = item['width'] * x_scale
            height = item['height'] * y_scale
            item_type = item['type']

            color = "gray" if item_type.lower() == "table" else "lightblue" if item_type.lower() == "window" else "brown"
            self.canvas.create_rectangle(x, y, x + width, y + height, fill=color, outline="black")
            self.canvas.create_text(x + width / 2, y + height / 2, text=item_type.capitalize(), fill="white")

    def apply_edit(self):
        edit_command = self.command_entry.get()
        if not self.layout_data:
            print("No existing layout to edit.")
            return

        prompt = (
            f"Modify the current layout based on this command: '{edit_command}'. "
            f"Here is the current layout data:\n"
            f"{self.layout_data}\n"
            f"Please remove, add, or move items exactly as instructed. "
            f"Provide the updated layout in the following exact format, strictly adhering to it:\n"
            f"Item: [Type]\nCoordinates (x, y): ([value], [value])\nDimensions (width, height): [value] x [value]\n"
            f"All items should be listed in this format with no additional explanations or information."
        )

        response = self.generate_text(prompt)
        if response:
            new_layout_data = self.parse_layout(response)
            if new_layout_data:
                self.layout_data = new_layout_data
                self.display_layout()
            else:
                print("Failed to parse updated layout.")
        else:
            print("Failed to apply edit.")


# Initialize Tkinter window
root = tk.Tk()
app = RoomLayoutApp(root)
root.mainloop()
