import tkinter as tk
from PIL import Image, ImageTk  # You'll need to install Pillow: pip install Pillow
import numpy as np
import random
import os

class Game2048:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("2048 Game")
        self.window.geometry("400x500")
        self.window.resizable(False, False)
        self.grid = np.zeros((4, 4), dtype=int)
        
        # Background color for empty tiles
        self.empty_color = "#cdc1b4"
        
        self.colors = {
            0: "#cdc1b4", 2: "#eee4da", 4: "#ede0c8", 8: "#f2b179",
            16: "#f59563", 32: "#f67c5f", 64: "#f65e3b", 128: "#edcf72",
            256: "#edcc61", 512: "#edc850", 1024: "#edc53f", 2048: "#edc22e"
        }
        
        # Load tile images and grid background before UI initialization
        self.images = {}
        self.load_grid_background()
        self.load_images()
        
        # Initialize UI components
        self.init_ui()
        
        self.spawn_tile()
        self.spawn_tile()
        self.update_ui()

        self.window.bind("<Key>", self.handle_keypress)
        self.window.mainloop()
    
    def load_grid_background(self):
        """Load or create the grid background image"""
        image_folder = os.path.join(os.path.dirname(__file__), "images")
        os.makedirs(image_folder, exist_ok=True)
        
        bg_path = os.path.join(image_folder, "grid_background.png")
        if not os.path.exists(bg_path):
            try:
                # Create a basic grid background if one doesn't exist
                bg_img = Image.new('RGBA', (360, 360), (187, 173, 160, 255))  # Main grid background color
                
                # Draw grid cells
                for i in range(4):
                    for j in range(4):
                        # Create a rounded rectangle for each cell
                        cell = Image.new('RGBA', (80, 80), (205, 193, 180, 255))  # Empty cell color
                        bg_img.paste(cell, (j*90+5, i*90+5), mask=None)
                
                bg_img.save(bg_path)
                print(f"Created grid background image at: {bg_path}")
            except Exception as e:
                print(f"Error creating grid background: {e}")
                self.grid_background = None
                return
        
        try:
            img = Image.open(bg_path)
            self.grid_background = ImageTk.PhotoImage(img)
            print("Successfully loaded grid background image")
        except Exception as e:
            print(f"Error loading grid background: {e}")
            self.grid_background = None
    
    def init_ui(self):
        # Create main frame with appropriate size for the grid
        self.frame = tk.Frame(self.window, bg="#bbada0", width=370, height=370)
        self.frame.pack(pady=20)
        self.frame.pack_propagate(False)  # Prevent frame from shrinking to fit children
        
        # Add grid background image first
        if hasattr(self, 'grid_background') and self.grid_background:
            self.bg_label = tk.Label(self.frame, image=self.grid_background, bg="#bbada0")
            self.bg_label.place(x=0, y=0)
            
            # Create a label at the bottom for game info
            info_label = tk.Label(self.window, text="Use arrow keys or WASD to move tiles",
                                 font=("Arial", 10), bg=self.window.cget('bg'))
            info_label.pack(pady=10)
        
        # Create tile labels with consistent size
        self.tiles = []
        for i in range(4):
            row_tiles = []
            for j in range(4):
                # Create tile labels that will overlay on the grid
                tile = tk.Label(self.frame, text="", font=("Arial", 20, "bold"), 
                              bg=self.empty_color, compound="center",
                              width=4, height=2)
                # Use place instead of grid to precisely position over the background
                tile.place(x=j*90+5, y=i*90+5, width=80, height=80)
                row_tiles.append(tile)
            self.tiles.append(row_tiles)

    def load_images(self):
        """Load all tile images from the images folder"""
        # Path to images folder - create if it doesn't exist
        image_folder = os.path.join(os.path.dirname(__file__), "images")
        os.makedirs(image_folder, exist_ok=True)
        
        # Create empty tile image if it doesn't exist
        empty_tile_path = os.path.join(image_folder, "empty.png")
        if not os.path.exists(empty_tile_path):
            try:
                # Create a blank transparent image for empty tiles
                empty_img = Image.new('RGBA', (80, 80), (205, 193, 180, 255))
                empty_img.save(empty_tile_path)
                print(f"Created empty tile image at: {empty_tile_path}")
            except Exception as e:
                print(f"Error creating empty tile image: {e}")
        
        # Load the empty tile image
        try:
            img = Image.open(empty_tile_path)
            img = img.resize((80, 80), Image.Resampling.LANCZOS)
            self.images[0] = ImageTk.PhotoImage(img)
            print("Successfully loaded empty tile image")
        except Exception as e:
            print(f"Error loading empty tile image: {e}")
        
        # Print the absolute path to help troubleshoot
        print(f"Looking for images in: {os.path.abspath(image_folder)}")
        
        # List all files in the images directory to verify
        try:
            files_in_dir = os.listdir(image_folder)
            print(f"Files found in image directory: {files_in_dir}")
        except Exception as e:
            print(f"Error listing directory: {e}")
        
        # Load images for each tile value
        for value in [2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048]:
            image_path = os.path.join(image_folder, f"{value}.png")
            if os.path.exists(image_path):
                try:
                    # Load and resize the image to fit the tiles
                    img = Image.open(image_path)
                    img = img.resize((80, 80), Image.Resampling.LANCZOS)
                    photo_img = ImageTk.PhotoImage(img)
                    self.images[value] = photo_img  # Store the PhotoImage
                    print(f"Successfully loaded image for tile {value}")
                except Exception as e:
                    print(f"Error loading image for tile {value}: {e}")
            else:
                print(f"Image file not found: {image_path}")
    
    def update_ui(self):
        """Update the UI with current grid values, using images instead of text"""
        for i in range(4):
            for j in range(4):
                value = self.grid[i, j]
                if value == 0 and 0 in self.images:
                    # Empty tile - visible but transparent
                    self.tiles[i][j].config(image=self.images[0], text="")
                elif value in self.images:
                    # Display the image for this value
                    self.tiles[i][j].config(image=self.images[value], text="")
                else:
                    # Fallback to text if image not available
                    self.tiles[i][j].config(image="", text=str(value) if value else "")
                
                # Make sure the tile is visible and properly placed
                self.tiles[i][j].lift()  # Ensure tile is above background
        
        self.window.update_idletasks()

    def spawn_tile(self):
        empty_cells = [(r, c) for r in range(4) for c in range(4) if self.grid[r, c] == 0]
        if empty_cells:
            r, c = random.choice(empty_cells)
            self.grid[r, c] = 2 if random.random() < 0.9 else 4
    
    def compress(self, row):
        # Fix: NumPy arrays don't have count() method
        # Convert row to list, count zeros, then create new row
        row_list = list(row)
        zero_count = row_list.count(0)
        new_row = [num for num in row_list if num != 0] + [0] * zero_count
        return np.array(new_row)
    
    def merge(self, row):
        for i in range(3):
            if row[i] == row[i+1] and row[i] != 0:
                row[i] *= 2
                row[i+1] = 0
        return row

    def move(self, direction):
        original_grid = self.grid.copy()
        if direction == 'up':
            self.grid = self.grid.T
            for i in range(4):
                self.grid[i] = self.compress(self.grid[i])
                self.grid[i] = self.merge(self.grid[i])
                self.grid[i] = self.compress(self.grid[i])
            self.grid = self.grid.T
        elif direction == 'down':
            self.grid = self.grid.T
            for i in range(4):
                self.grid[i] = self.compress(self.grid[i][::-1])[::-1]
                self.grid[i] = self.merge(self.grid[i][::-1])[::-1]
                self.grid[i] = self.compress(self.grid[i][::-1])[::-1]
            self.grid = self.grid.T
        elif direction == 'left':
            for i in range(4):
                self.grid[i] = self.compress(self.grid[i])
                self.grid[i] = self.merge(self.grid[i])
                self.grid[i] = self.compress(self.grid[i])
        elif direction == 'right':
            for i in range(4):
                self.grid[i] = self.compress(self.grid[i][::-1])[::-1]
                self.grid[i] = self.merge(self.grid[i][::-1])[::-1]
                self.grid[i] = self.compress(self.grid[i][::-1])[::-1]
        
        if not np.array_equal(original_grid, self.grid):
            self.spawn_tile()
        self.update_ui()
        if self.is_game_over():
            self.show_game_over()
    
    def is_game_over(self):
        if 0 in self.grid:
            return False
        for i in range(4):
            for j in range(3):
                if self.grid[i, j] == self.grid[i, j+1] or self.grid[j, i] == self.grid[j+1, i]:
                    return False
        return True

    def show_game_over(self):
        game_over_window = tk.Toplevel(self.window)
        game_over_window.title("Game Over")
        game_over_window.geometry("200x100")
        tk.Label(game_over_window, text="Game Over!", font=("Arial", 16, "bold")).pack(pady=10)
        tk.Button(game_over_window, text="Restart", command=lambda: [game_over_window.destroy(), self.restart_game()]).pack()

    def restart_game(self):
        self.grid = np.zeros((4, 4), dtype=int)
        self.spawn_tile()
        self.spawn_tile()
        self.update_ui()

    def handle_keypress(self, event):
        if event.keysym in ("Up", "w"):
            self.move('up')
        elif event.keysym in ("Down", "s"):
            self.move('down')
        elif event.keysym in ("Left", "a"):
            self.move('left')
        elif event.keysym in ("Right", "d"):
            self.move('right')

if __name__ == "__main__":
    Game2048()
