import tkinter as tk
import pyperclip
from tkinter import Menu
from PIL import Image, ImageTk, ImageDraw, ImageGrab
from openai import OpenAI
import requests
import os
from io import BytesIO
import io
from rembg import remove
import ctypes
from ctypes import wintypes
import win32clipboard


# Initialize the OpenAI client
client = OpenAI(api_key="ENTER OPENAI API KEY")

# Global variables
img = None  # Will hold the current PIL image
img_tk = None  # Will hold the current ImageTk image for display
edit_mode_enabled = False
classification_enabled = True
latest_image_path = None
unaltered_image_path = None

# Scale factor for resizing the display image
SCALE_FACTOR = 0.5

# Create directory for saving images if not exists
if not os.path.exists("masked_images"):
    os.makedirs("masked_images")


# Flag to track whether we are in edit mode
edit_mode_enabled = False

# Paths for the images
#latest_image_path = "masked_images/original_image.png"  # The latest edited image or original image
#unaltered_image_path = "masked_images/unaltered_image.png"  # Unaltered image without transparency

# Create directory for saving images
if not os.path.exists("masked_images"):
    os.makedirs("masked_images")

# Function to handle dragging
def on_drag_start(event):
    canvas.scan_mark(event.x, event.y)

def on_drag_motion(event):
    canvas.scan_dragto(event.x, event.y, gain=1)

# Function to copy image to the system clipboard (Windows only)
def copy_image_to_clipboard():
    # Load the image with RGBA to retain transparency
    with Image.open(latest_image_path) as temp_image:
        temp_image = temp_image.convert("RGBA")
        
        # Save the image as PNG to preserve transparency
        output = BytesIO()
        temp_image.save(output, format="PNG")
        data = output.getvalue()
        output.close()
        
        # Open clipboard and set the PNG data
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.RegisterClipboardFormat("PNG"), data)
        win32clipboard.CloseClipboard()

# Function to show context menu on right-click
def show_context_menu(event):
    if img is not None:
        context_menu = tk.Menu(root, tearoff=0)
        context_menu.add_command(label="Copy", command=copy_image_to_clipboard)
        context_menu.post(event.x_root, event.y_root)

# Function to generate a new image based on prompt
def generate_image(prompt, model="dall-e-2", size="1024x1024", n=1, quality="standard"):
    try:
        # Call the OpenAI API to generate an image
        response = client.images.generate(
            model=model,
            prompt=prompt,
            size=size,
            quality=quality,
            n=n
        )
        # Get the image URL from the response
        image_url = response.data[0].url
        return image_url
    except Exception as e:
        print(f"Failed to generate image: {e}")
        return None

# Display the image and show the mask creation button
def display_image(image):
    global img, img_tk
    try:
        img = image  # Update the global img with the new image
        original_width, original_height = img.size
        new_width = int(original_width * SCALE_FACTOR)
        new_height = int(original_height * SCALE_FACTOR)
        img_resized = img.resize((new_width, new_height), Image.ANTIALIAS)

        canvas.config(width=new_width, height=new_height)
        img_tk = ImageTk.PhotoImage(img_resized)
        canvas.img_tk = img_tk  # Keep a reference to prevent garbage collection
        canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)

        root.geometry(f"{new_width}x{new_height + 250}")
        highlight_button.pack()

        # Bind right-click to show context menu for copying the image
        canvas.bind("<Button-3>", show_context_menu)

    except Exception as e:
        print(f"Failed to display image: {e}")

# Reset the image to its unaltered state
def reset_image():
    global img, edit_mode_enabled
    img = Image.open(unaltered_image_path).convert("RGBA")
    display_image(img)
    edit_mode_enabled = False
    new_image_button.pack_forget()

    # Re-enable the "Highlight and Make Transparent" button
    highlight_button.config(state="normal")
    # Disable the "Reset" button
    reset_button.config(state="disabled")

    # Unbind mouse events to disable selection mode
    canvas.unbind("<ButtonPress-1>")
    canvas.unbind("<B1-Motion>")
    canvas.unbind("<ButtonRelease-1>")

# Reset to new image creation mode
def reset_to_new_image_mode():
    global edit_mode_enabled, latest_image_path, unaltered_image_path
    edit_mode_enabled = False
    latest_image_path = "masked_images/original_image.png"
    unaltered_image_path = latest_image_path
    print("New image creation mode enabled.")

    # Hide buttons
    new_image_button.pack_forget()
    highlight_button.pack_forget()
    reset_button.pack_forget()

    # Unbind mouse events
    canvas.unbind("<ButtonPress-1>")
    canvas.unbind("<B1-Motion>")
    canvas.unbind("<ButtonRelease-1>")

    # Clear the canvas
    canvas.delete("all")

    # Reset flags and states
    highlight_button.config(state="normal")
    reset_button.config(state="disabled")

    # Clear the prompt box
    prompt_box.delete("1.0", tk.END)

# Make a specific area of the image transparent for inpainting
def make_transparent(start, end):
    global img, edit_mode_enabled, latest_image_path, unaltered_image_path

    # Save the current image as the unaltered image
    img.save(unaltered_image_path, "PNG")

    # Adjust the start and end points according to the scale factor
    start = (int(start[0] / SCALE_FACTOR), int(start[1] / SCALE_FACTOR))
    end = (int(end[0] / SCALE_FACTOR), int(end[1] / SCALE_FACTOR))

    # Calculate the midpoint and radius for the circular mask
    center_x = (start[0] + end[0]) // 2
    center_y = (start[1] + end[1]) // 2
    radius = int((((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2) ** 0.5) / 2)

    # Open a copy of the latest image (this will be the mask after transparency)
    mask_img = Image.open(latest_image_path).convert("RGBA")
    img_copy_data = mask_img.load()

    # Create a mask to apply transparency
    mask = Image.new("L", mask_img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse(
        [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
        fill=255,
    )

    # Apply the transparency to the displayed image (img) and the mask image
    img_data = img.load()
    for y in range(mask_img.height):
        for x in range(mask_img.width):
            if mask.getpixel((x, y)) > 0:
                img_copy_data[x, y] = (*img_copy_data[x, y][:3], 0)
                img_data[x, y] = (*img_data[x, y][:3], 0)

    # Save the mask image
    mask_img.save("masked_images/mask.png", "PNG")

    # Save the latest edited image
    img.save("masked_images/edited_image.png", "PNG")
    latest_image_path = "masked_images/edited_image.png"

    # Display the updated image with transparency
    display_image(img)

    # Enable edit mode for inpainting
    edit_mode_enabled = True

    # Show the "New Image" button
    new_image_button.pack()

    # Disable selection mode after one selection
    canvas.unbind("<ButtonPress-1>")
    canvas.unbind("<B1-Motion>")
    canvas.unbind("<ButtonRelease-1>")

def enable_highlight_mode():
    highlight_button.config(state="disabled")  # Disable the button after clicking it
    canvas.bind("<ButtonPress-1>", on_mouse_down)
    canvas.bind("<B1-Motion>", on_mouse_move)
    canvas.bind("<ButtonRelease-1>", on_mouse_up)
    
    reset_button.config(state="normal")  # Enable the "Reset" button
    reset_button.pack()
    
    new_image_button.pack()  # Show the "New Image" button immediately

# Mouse event functions to draw a selection circle
start_x, start_y, circle_id = None, None, None



def on_mouse_down(event):
    global start_x, start_y, circle_id
    start_x, start_y = event.x, event.y
    circle_id = canvas.create_oval(start_x, start_y, start_x, start_y, outline="red")

def on_mouse_move(event):
    global circle_id
    if circle_id:
        canvas.coords(circle_id, start_x, start_y, event.x, event.y)

def on_mouse_up(event):
    global start_x, start_y, circle_id
    if circle_id:
        make_transparent((start_x, start_y), (event.x, event.y))
        canvas.delete(circle_id)
        circle_id = None

# Handle image generation or inpainting based on the current mode
def on_send():
    global img, img_copy, latest_image_path, unaltered_image_path, edit_mode_enabled
    prompt = prompt_box.get("1.0", tk.END).strip()
    if prompt:
        # Prepare the classification prompt
        classification_prompt = f"""Read the following text, and determine whether the user wishes to create an image of a room, an inpaint/room addition image/room correction image, or just an image of an object. If you determine the user wishes to create an image of a room, only respond '1'. If you determine the user wishes to create an inpaint or room addition image or room correction image only respond '2'. If you determine the user wishes to create just an image of an object, only respond '3'.

User prompt: {prompt}
"""
        try:
            # Send the classification prompt to the OpenAI API
            response = client.completions.create(
                model="gpt-3.5-turbo-instruct",
                prompt=classification_prompt,
                max_tokens=5,
                temperature=0
            )
            # Extract and strip the response text
            chatgpt_response = response.choices[0].text.strip()
            print(f"ChatGPT classified response: '{chatgpt_response}'")  # Debug output

            # Handle response based on classification
            if chatgpt_response == '1':
                if edit_mode_enabled:
                    # Edit the existing image using the mask
                    print("Editing image with the prompt:", prompt)
                    try:
                        response = client.images.edit(
                            model="dall-e-2",
                            image=open(latest_image_path, "rb"),
                            mask=open("masked_images/mask.png", "rb"),
                            prompt=prompt,
                            n=1,
                            size="1024x1024"
                        )
                        image_url = response.data[0].url
                        # Load and display the edited image
                        response = requests.get(image_url)
                        img_data = response.content
                        img = Image.open(BytesIO(img_data)).convert("RGBA")

                        # Save the newly edited image as the latest image
                        img.save("masked_images/edited_image.png", "PNG")
                        latest_image_path = "masked_images/edited_image.png"
                        unaltered_image_path = latest_image_path

                        # Display the newly edited image
                        display_image(img)

                        # Re-enable the "Highlight and Make Transparent" button
                        highlight_button.config(state="normal")
                        # Disable the "Reset" button
                        reset_button.config(state="disabled")
                    except Exception as e:
                        print(f"Failed to edit image: {e}")
                else:
                    # Generate a new image
                    print("Generating new image with the prompt:", prompt)
                    image_url = generate_image(prompt, model="dall-e-2", size="1024x1024", n=1, quality="standard")
                    if image_url:
                        response = requests.get(image_url)
                        img_data = response.content
                        img = Image.open(BytesIO(img_data)).convert("RGBA")
                        img_copy = img.copy()

                        # Save the original image as the latest image for future edits
                        img.save("masked_images/original_image.png", "PNG")
                        latest_image_path = "masked_images/original_image.png"
                        unaltered_image_path = latest_image_path

                        # Display the image
                        display_image(img)
                        new_image_button.pack_forget()
            elif chatgpt_response == '2':
                # Enter highlight mode for inpainting
                print("Option 2 selected: Entering inpainting mode.")
                enable_highlight_mode()
            elif chatgpt_response == '3':
                # Hide all buttons except the "Send" button
                highlight_button.pack_forget()
                highlight_button.config(state="disabled")
                reset_button.pack_forget()
                new_image_button.pack_forget()

                # Determine the most contrasting background color
                color_prompt = f"""Read the following prompt and determine what color, out of white, black, or green, would most contrast the image as a background, depending on the colors within the prompt. If there are no colors listed in the prompt or if you determine black to be the most contrasting, say only 'black'. If you determine white to be most contrasting, return 'white'. If you determine green to be most contrasting, return 'green':

User prompt: {prompt}
"""
                try:
                    color_response = client.completions.create(
                        model="gpt-3.5-turbo-instruct",
                        prompt=color_prompt,
                        max_tokens=5,
                        temperature=0
                    )
                    background_color = color_response.choices[0].text.strip().lower()
                    print(f"Background color chosen by ChatGPT: '{background_color}'")

                    # Validate the background color response
                    if background_color not in ['black', 'white', 'green']:
                        background_color = 'black'  # Default to black if response is unexpected

                    # Create the modified prompt with the chosen background color
                    modified_prompt = f"{prompt} flat against a solid {background_color} background"
                    print("Generating image with modified prompt:", modified_prompt)

                    # Generate the image with the modified prompt
                    image_url = generate_image(modified_prompt, model="dall-e-2", size="1024x1024", n=1, quality="standard")
                    if image_url:
                        response = requests.get(image_url)
                        img_data = response.content

                        # Remove the background using rembg
                        img_without_bg = remove(img_data)  # Remove background
                        img = Image.open(io.BytesIO(img_without_bg)).convert("RGBA")

                        # Save and display the image without background
                        img.save("masked_images/without_bg_image.png", "PNG")
                        latest_image_path = "masked_images/without_bg_image.png"
                        unaltered_image_path = latest_image_path
                        display_image(img)
                except Exception as e:
                    print(f"Failed to determine background color or remove background: {e}")
            else:
                # Handle unexpected responses 
                print("Unexpected response from ChatGPT:", chatgpt_response)
                print("Please try rephrasing the prompt or check for input errors.")
        except Exception as e:
            print(f"Failed to classify prompt or generate image: {e}")
    else:
        print("Input Required: Please enter a prompt.")

# Initialize the Tkinter window
root = tk.Tk()
root.title("Image Generator")
root.geometry("512x500")

# Create a textbox for the prompt input
prompt_box = tk.Text(root, height=4, width=50)
prompt_box.pack(pady=10)

# Create a send button for generating the image or submitting an edit
send_button = tk.Button(root, text="Send", command=on_send)
send_button.pack(pady=10)

# Create a canvas to display the image
canvas = tk.Canvas(root)
canvas.pack()

# Button to initiate highlight and mask creation
highlight_button = tk.Button(root, text="Highlight and Make Transparent", command=enable_highlight_mode)
highlight_button.pack_forget()  # Initially hidden

# Button to reset the image
reset_button = tk.Button(root, text="Reset Image", command=reset_image)
reset_button.pack_forget()

# Button to reset to new image creation mode
new_image_button = tk.Button(root, text="New Image", command=reset_to_new_image_mode)
new_image_button.pack_forget()

# Bind canvas for drag and drop
# canvas.bind("<ButtonPress-1>", on_drag_start)
# canvas.bind("<B1-Motion>", on_drag_motion)

# Bind right-click to show context menu
canvas.bind("<Button-3>", show_context_menu)


# Start the Tkinter event loop
root.mainloop()
