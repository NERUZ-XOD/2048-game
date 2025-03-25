import tkinter as tk
from PIL import Image, ImageTk  # You'll need to install Pillow: pip install Pillow
import numpy as np
import random
import os
import json
import pygame
from tkinter import messagebox

class Game2048:
    def __init__(self, master):
        self.window = master
        self.window.title("2048 Retro Game")
        self.window.geometry("400x600")
        self.window.resizable(False, False)
        self.grid = np.zeros((4, 4), dtype=int)
        
        # Score tracking
        self.current_score = 0
        self.high_score = self.load_high_score()
        
        # Initialize pygame for sound effects
        pygame.mixer.init()
        
        # Load sound effects
        self.sound_folder = os.path.join(os.path.dirname(__file__), "sounds")
        os.makedirs(self.sound_folder, exist_ok=True)
        
        self.sounds = {
            'move': None,
            'merge': None,
            'game_over': None,
            'win': None
        }
        
        self.load_sounds()
        
        # Background color for empty tiles
        self.empty_color = "#bbada0"
        
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
    
    def load_high_score(self):
        """Load high score from file"""
        try:
            with open('high_score.json', 'r') as f:
                data = json.load(f)
                return data.get('high_score', 0)
        except (FileNotFoundError, json.JSONDecodeError):
            return 0
    
    def save_high_score(self):
        """Save high score to file"""
        try:
            with open('high_score.json', 'w') as f:
                json.dump({'high_score': int(self.high_score)}, f)
        except Exception as e:
            print(f"Error saving high score: {e}")
    
    def load_sounds(self):
        """Load sound effects"""
        # Check if sound files exist, if not create placeholder files
        sound_files = {
            'move': 'move.wav',
            'merge': 'merge.wav',
            'game_over': 'game_over.wav',
            'win': 'win.wav'
        }
        
        # Create placeholder sound files if they don't exist
        for sound_key, sound_file in sound_files.items():
            sound_path = os.path.join(self.sound_folder, sound_file)
            if not os.path.exists(sound_path):
                try:
                    # Create an empty WAV file (1 second of silence)
                    from scipy.io import wavfile
                    import numpy as np
                    
                    sample_rate = 44100  # standard sample rate
                    duration = 0.1  # duration in seconds
                    samples = np.zeros(int(sample_rate * duration))  # silent audio
                    
                    wavfile.write(sound_path, sample_rate, samples.astype(np.int16))
                    print(f"Created placeholder sound file: {sound_path}")
                except ImportError:
                    print("SciPy not installed, cannot create placeholder sound files")
                except Exception as e:
                    print(f"Error creating sound file {sound_key}: {e}")
        
        # Now load the sound files (either existing or newly created)
        for sound_key, sound_file in sound_files.items():
            sound_path = os.path.join(self.sound_folder, sound_file)
            if os.path.exists(sound_path):
                try:
                    self.sounds[sound_key] = pygame.mixer.Sound(sound_path)
                    print(f"Loaded sound: {sound_key}")
                except Exception as e:
                    print(f"Error loading sound {sound_key}: {e}")
            else:
                print(f"Sound file not found: {sound_path}")
    
    def play_sound(self, sound_key):
        """Play a sound effect"""
        if hasattr(self, 'music_on') and self.music_on and sound_key in self.sounds and self.sounds[sound_key]:
            try:
                self.sounds[sound_key].play()
            except Exception as e:
                print(f"Error playing sound {sound_key}: {e}")
    
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
        # Create main frame for the game grid
        self.frame = tk.Frame(self.window, bg="#bbada0", width=370, height=370)
        self.frame.pack(pady=20)
        self.frame.pack_propagate(False)  # Prevent frame from shrinking to fit children
        
        # Add grid background image first
        if hasattr(self, 'grid_background') and self.grid_background:
            self.bg_label = tk.Label(self.frame, image=self.grid_background, bg="#bbada0")
            self.bg_label.place(x=0, y=0)
        
        # Score display
        self.score_frame = tk.Frame(self.window, bg="#bbada0")
        self.score_frame.pack(fill="x", padx=20, pady=10)
        
        self.score_label = tk.Label(self.score_frame, text=f"Score: {self.current_score}", 
                                   font=("Arial", 14, "bold"), bg="#bbada0", fg="#ffffff")
        self.score_label.pack(side="left", padx=10)
        
        self.high_score_label = tk.Label(self.score_frame, text=f"Best: {self.high_score}", 
                                        font=("Arial", 14, "bold"), bg="#bbada0", fg="#ffffff")
        self.high_score_label.pack(side="right", padx=10)
        
        # Create tile labels with consistent size
        self.tiles = []
        for i in range(4):
            row_tiles = []
            for j in range(4):
                # Create tile labels that will overlay on the grid
                # Use a frame with a transparent background for empty cells
                tile = tk.Label(self.frame, text="", font=("Arial", 20, "bold"), 
                              bg=self.empty_color, compound="center",
                              width=4, height=2, borderwidth=0, highlightthickness=0)
                # Use place instead of grid to precisely position over the background
                tile.place(x=j*90+5, y=i*90+5, width=80, height=80)
                row_tiles.append(tile)
            self.tiles.append(row_tiles)
        
        # Bottom menu
        self.bottom_frame = tk.Frame(self.window, bg="#bbada0")
        self.bottom_frame.pack(fill="x", side="bottom", padx=20, pady=20)
        
        self.save_button = tk.Button(self.bottom_frame, text="Save Game", 
                                    command=self.save_game, font=("Arial", 12),
                                    bg="#8f7a66", fg="#ffffff")
        self.save_button.pack(side="left", padx=10)
        
        self.help_button = tk.Button(self.bottom_frame, text="Help", 
                                    command=self.show_help, font=("Arial", 12),
                                    bg="#8f7a66", fg="#ffffff")
        self.help_button.pack(side="left", padx=10)
        
        self.quit_button = tk.Button(self.bottom_frame, text="Quit", 
                                    command=self.quit_game, font=("Arial", 12),
                                    bg="#8f7a66", fg="#ffffff")
        self.quit_button.pack(side="right", padx=10)
        
        # Music control
        self.music_button = tk.Button(self.bottom_frame, text="🔊", 
                                     command=self.toggle_music, font=("Arial", 12),
                                     bg="#8f7a66", fg="#ffffff", width=2)
        self.music_button.pack(side="right", padx=10)
        
        self.music_on = True

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
                if value == 0:
                    # Make empty tiles completely invisible
                    self.tiles[i][j].place_forget()  # Remove from view
                else:
                    # Make sure the tile is visible and properly placed
                    self.tiles[i][j].place(x=j*90+5, y=i*90+5, width=80, height=80)
                    
                    if value in self.images:
                        # Display the image for this value
                        self.tiles[i][j].config(image=self.images[value], text="", bg=self.colors.get(value, "#cdc1b4"))
                    else:
                        # Fallback to text if image not available
                        self.tiles[i][j].config(image="", text=str(value) if value else "", bg=self.colors.get(value, "#cdc1b4"))
        
        # Update score display
        self.score_label.config(text=f"Score: {self.current_score}")
        self.high_score_label.config(text=f"Best: {self.high_score}")
        
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
                self.current_score += row[i]  # Update score when tiles merge
                if row[i] == 2048:
                    self.show_win_message()
                self.play_sound('merge')
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
        
        # Check if the grid changed
        if not np.array_equal(original_grid, self.grid):
            self.play_sound('move')
            self.spawn_tile()
            self.update_ui()
            
            # Update high score if current score is higher
            if self.current_score > self.high_score:
                self.high_score = self.current_score
                self.save_high_score()
            
            # Check if game is over
            if self.is_game_over():
                self.play_sound('game_over')
                self.show_game_over()
    
    def is_game_over(self):
        # Check if there are any empty cells
        if 0 in self.grid:
            return False
        
        # Check if there are any adjacent same values
        for i in range(4):
            for j in range(3):
                if self.grid[i][j] == self.grid[i][j+1]:
                    return False
        
        for i in range(3):
            for j in range(4):
                if self.grid[i][j] == self.grid[i+1][j]:
                    return False
        
        return True
    
    def show_win_message(self):
        """Show a win message when the player reaches 2048"""
        self.play_sound('win')
        messagebox.showinfo("Congratulations!", "You've reached 2048! You can continue playing to achieve a higher score.")
    
    def show_game_over(self):
        """Show game over message"""
        response = messagebox.askyesno("Game Over", f"Game Over! Your score: {self.current_score}\nDo you want to play again?")
        if response:
            self.restart_game()
        else:
            self.quit_game()

    def restart_game(self):
        self.grid = np.zeros((4, 4), dtype=int)
        self.current_score = 0
        self.spawn_tile()
        self.spawn_tile()
        self.update_ui()
    
    def save_game(self):
        """Save the current game state"""
        # Convert NumPy arrays and int64 values to standard Python types
        grid_list = [[int(cell) for cell in row] for row in self.grid.tolist()]
        
        game_state = {
            'grid': grid_list,
            'score': int(self.current_score),
            'high_score': int(self.high_score)
        }
        
        try:
            with open('saved_game.json', 'w') as f:
                json.dump(game_state, f)
            messagebox.showinfo("Game Saved", "Your game has been saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save game: {e}")
    
    def load_game(self):
        """Load a saved game state"""
        try:
            with open('saved_game.json', 'r') as f:
                game_state = json.load(f)
                
            self.grid = np.array(game_state['grid'], dtype=int)
            self.current_score = int(game_state['score'])
            self.high_score = int(game_state['high_score'])
            self.update_ui()
            messagebox.showinfo("Game Loaded", "Your saved game has been loaded successfully!")
            return True
        except (FileNotFoundError, json.JSONDecodeError):
            messagebox.showinfo("No Saved Game", "No saved game found. Starting a new game.")
            return False
        except Exception as e:
            messagebox.showerror("Error", f"Could not load game: {e}")
            return False
    
    def show_help(self):
        """Show help information"""
        help_text = """
        How to Play 2048:
        
        - Use arrow keys or WASD to move tiles
        - When two tiles with the same number touch, they merge into one
        - Try to reach the 2048 tile!
        
        Controls:
        - Arrow keys or WASD: Move tiles
        - Save Game: Save your current progress
        - Help: Show this help message
        - Quit: Exit the game
        - 🔊: Toggle sound on/off
        """
        messagebox.showinfo("How to Play", help_text)
    
    def toggle_music(self):
        """Toggle music on/off"""
        self.music_on = not self.music_on
        if self.music_on:
            self.music_button.config(text="🔊")
            # Resume music if it was playing
        else:
            self.music_button.config(text="🔇")
            # Pause music if it was playing
    
    def quit_game(self):
        """Exit to main menu"""
        if messagebox.askyesno("Quit Game", "Are you sure you want to quit? Your progress will be lost unless saved."):
            self.window.destroy()
            root = tk.Tk()
            root.title("2048 Retro Game")
            root.geometry("400x600")
            MainMenu(root)
    
    def handle_keypress(self, event):
        if event.keysym in ("Up", "w"):
            self.move('up')
        elif event.keysym in ("Down", "s"):
            self.move('down')
        elif event.keysym in ("Left", "a"):
            self.move('left')
        elif event.keysym in ("Right", "d"):
            self.move('right')


class MainMenu:
    def __init__(self, master):
        self.master = master
        self.master.title("2048 Retro Game")
        self.frame = tk.Frame(master, bg="#000000", width=400, height=600)
        self.frame.pack(fill="both", expand=True)
        
        # Load high score
        self.high_score = self.load_high_score()
        
        # Load pixel art background if available
        self.load_background()
        
        # High Score Display
        self.high_score_label = tk.Label(self.frame, text=f"High Score: {self.high_score}", 
                                        font=("Arial", 16, "bold"), fg="#FFFFFF", bg="#000000")
        self.high_score_label.pack(pady=20)
        
        # Title
        self.title_label = tk.Label(self.frame, text="2048 RETRO", 
                                   font=("Arial", 36, "bold"), fg="#FFD700", bg="#000000")
        self.title_label.pack(pady=20)
        
        # Main Menu Buttons
        button_frame = tk.Frame(self.frame, bg="#000000")
        button_frame.pack(pady=20)
        
        button_style = {"font": ("Arial", 14), "width": 15, "height": 2, 
                       "bg": "#333333", "fg": "#FFFFFF", "activebackground": "#555555"}
        
        self.new_game_button = tk.Button(button_frame, text="New Game", 
                                        command=self.start_new_game, **button_style)
        self.new_game_button.pack(pady=10)
        
        self.continue_button = tk.Button(button_frame, text="Continue", 
                                        command=self.continue_game, **button_style)
        self.continue_button.pack(pady=10)
        
        self.how_to_play_button = tk.Button(button_frame, text="How to Play", 
                                           command=self.show_how_to_play, **button_style)
        self.how_to_play_button.pack(pady=10)
        
        self.exit_button = tk.Button(button_frame, text="Exit", 
                                    command=self.exit_game, **button_style)
        self.exit_button.pack(pady=10)
        
        # Initialize pygame for sound effects if not already initialized
        if not pygame.mixer.get_init():
            pygame.mixer.init()
    
    def load_background(self):
        """Load pixel art background for the main menu"""
        image_folder = os.path.join(os.path.dirname(__file__), "images")
        os.makedirs(image_folder, exist_ok=True)
        
        bg_path = os.path.join(image_folder, "menu_background.png")
        if os.path.exists(bg_path):
            try:
                img = Image.open(bg_path)
                img = img.resize((400, 600), Image.Resampling.LANCZOS)
                self.bg_image = ImageTk.PhotoImage(img)
                
                # Create a label for the background image
                bg_label = tk.Label(self.frame, image=self.bg_image)
                bg_label.place(x=0, y=0, relwidth=1, relheight=1)
                
                # Make sure other widgets appear on top of the background
                self.frame.lift()
            except Exception as e:
                print(f"Error loading menu background: {e}")
    
    def load_high_score(self):
        """Load high score from file"""
        try:
            with open('high_score.json', 'r') as f:
                data = json.load(f)
                return data.get('high_score', 0)
        except (FileNotFoundError, json.JSONDecodeError):
            return 0

    def start_new_game(self):
        self.frame.destroy()
        Game2048(self.master)

    def continue_game(self):
        """Load the last saved game state"""
        self.frame.destroy()
        game = Game2048(self.master)
        if not game.load_game():
            # If loading fails, the game will start a new game
            pass

    def show_how_to_play(self):
        help_text = """
        How to Play 2048:
        
        - Use arrow keys or WASD to move tiles
        - When two tiles with the same number touch, they merge into one
        - Try to reach the 2048 tile!
        
        Controls:
        - Arrow keys or WASD: Move tiles
        - Save Game: Save your current progress
        - Help: Show this help message
        - Quit: Exit the game
        - 🔊: Toggle sound on/off
        """
        messagebox.showinfo("How to Play", help_text)

    def exit_game(self):
        self.master.quit()


if __name__ == "__main__":
    root = tk.Tk()
    root.title("2048 Retro Game")
    root.geometry("400x600")
    MainMenu(root)
    root.mainloop()
