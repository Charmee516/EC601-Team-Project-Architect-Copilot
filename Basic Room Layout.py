import tkinter as tk
from PIL import Image, ImageTk
import openai
import requests
from io import BytesIO

# Initialize OpenAI with your API key
openai.api_key = "api key"  # Replace with your actual OpenAI API key
import os
openai.api_key = os.getenv("OPENAI_API_KEY")


class RoomLayoutApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI-Generated Room Layout")
        self.root.geometry("600x700")

        # Room dimension input fields
        self.width_label = tk.Label(root, text="Room Width:")
        self.width_label.pack()
        self.width_entry = tk.Entry(root)
        self.width_entry.pack()

        self.height_label = tk.Label(root, text="Room Height:")
        self.height_label.pack()
        self.height_entry = tk.Entry(root)
        self.height_entry.pack()

        # Dropdown to select room type
        self.room_type_label = tk.Label(root, text="Select Room Type:")
        self.room_type_label.pack()

        self.room_type = tk.StringVar(root)
        self.room_type.set("Living Room")  # Default value
        self.room_type_dropdown = tk.OptionMenu(root, self.room_type, "Living Room", "Bedroom", "Kitchen", "Bathroom")
        self.room_type_dropdown.pack()

        # Button to generate layout
        self.generate_button = tk.Button(root, text="Generate AI Layout", command=self.generate_ai_layout)
        self.generate_button.pack(pady=10)

        # Canvas to display the generated image
        self.canvas = tk.Canvas(root, width=512, height=512, bg="white")
        self.canvas.pack(pady=20)

        # Placeholder for the AI-generated image
        self.generated_image = None

    def generate_ai_layout(self):
        # Get room type and create the prompt
        room_type = self.room_type.get()
        prompt = f"Generate a {room_type} layout with modern furniture and decorations."

        # Call OpenAI DALL·E API to generate the image
        image_url = self.generate_image(prompt)

        # If image generation was successful, display the image
        if image_url:
            self.display_image(image_url)
        else:
            print("Failed to generate the image.")

    def generate_image(self, prompt):
        try:
            # Call the DALL·E API to generate the image
            response = openai.Image.create(
                prompt=prompt,
                n=1,
                size="512x512"
            )
            # Extract the image URL from the response
            image_url = response['data'][0]['url']
            return image_url
        except Exception as e:
            print(f"Error generating image: {e}")
            return None

    def display_image(self, image_url):
        try:
            # Fetch the image from the URL
            response = requests.get(image_url)
            img_data = response.content

            # Load the image into PIL and resize it
            img = Image.open(BytesIO(img_data))
            img = img.resize((512, 512))

            # Convert the image to a format Tkinter can handle
            self.generated_image = ImageTk.PhotoImage(img)

            # Clear the canvas and display the new image
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.generated_image)
        except Exception as e:
            print(f"Error displaying image: {e}")


# Initialize the Tkinter window
root = tk.Tk()
app = RoomLayoutApp(root)
root.mainloop()


