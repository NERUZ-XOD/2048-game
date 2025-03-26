import tkinter as tk
from PIL import Image, ImageTk
import numpy as np
import random
import os
import json
import pygame
from tkinter import messagebox
import tkinter.font as tkFont
import time

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
        
        # Sound settings
        self.music_on = True  # Default to having sound on
        
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
        
        # Load custom fonts
        self.load_custom_fonts()
        
        # Background color for empty tiles
        self.empty_color = "#bbada0"
        
        self.colors = {
            0: "#cdc1b4", 2: "#eee4da", 4: "#ede0c8", 8: "#f2b179",
            16: "#f59563", 32: "#f67c5f", 64: "#f65e3b", 128: "#edcf72",
            256: "#edcc61", 512: "#edc850", 1024: "#edc53f", 2048: "#edc22e"
        }
        
        # Animation settings
        self.animation_speed = 15  # ms between animation frames
        self.animation_duration = 150  # total animation duration in ms
        self.animation_frames = self.animation_duration // self.animation_speed
        self.is_animating = False
        self.animation_queue = []
        self.last_grid = None
        self.grid_positions = [
            # Row 1
            [(25, 25), (117, 25), (209, 25), (301, 25)],
            # Row 2
            [(25, 117), (117, 117), (209, 117), (301, 117)],
            # Row 3
            [(25, 209), (117, 209), (209, 209), (301, 209)],
            # Row 4
            [(25, 301), (117, 301), (209, 301), (301, 301)]
        ]
        
        # Load tile images and grid background before UI initialization
        self.images = {}
        self.load_grid_background()
        self.load_images()
        
        # Initialize UI components
        self.init_ui()
        
        self.spawn_tile(animate=False)
        self.spawn_tile(animate=False)
        self.update_ui()

        self.window.bind("<Key>", self.handle_keypress)
    
    def init_ui(self):
        # Create main frame for the game grid
        self.frame = tk.Frame(self.window, bg="#bbada0", width=400, height=400)
        self.frame.pack(pady=20)
        self.frame.pack_propagate(False)  # Prevent frame from shrinking to fit children
        
        # Add grid background image first
        if hasattr(self, 'grid_background') and self.grid_background:
            self.bg_label = tk.Label(self.frame, image=self.grid_background, bg="#bbada0")
            self.bg_label.place(x=0, y=0, width=400, height=400)
        
        # Score display
        self.score_frame = tk.Frame(self.window, bg="#bbada0")
        self.score_frame.pack(fill="x", padx=20, pady=10)
        
        self.score_label = tk.Label(self.score_frame, text=f"Score: {self.current_score}", 
                                   font=("Press Start 2P", 12), bg="#bbada0", fg="#ffffff")
        self.score_label.pack(side="left", padx=10)
        
        self.high_score_label = tk.Label(self.score_frame, text=f"Best: {self.high_score}", 
                                        font=("Press Start 2P", 12), bg="#bbada0", fg="#ffffff")
        self.high_score_label.pack(side="right", padx=10)
        
        # Create tile labels with consistent size
        self.tiles = []
        
        # Precise measurements for grid alignment
        # These values are carefully tuned to match the grid background
        tile_size = 72  # Exact tile size as specified in memory
        
        # Fixed positions for each cell in the grid
        # These are manually tuned to match the grid background using the exact coordinates from memory
        
        for i in range(4):
            row_tiles = []
            for j in range(4):
                # Create tile labels that will overlay on the grid
                tile = tk.Label(self.frame, text="", font=("Press Start 2P", 16), 
                              bg=self.empty_color, compound="center",
                              width=4, height=2, borderwidth=0, highlightthickness=0)
                
                # Use the pre-defined positions for precise placement
                x_pos, y_pos = self.grid_positions[i][j]
                
                tile.place(x=x_pos, y=y_pos, width=tile_size, height=tile_size)
                row_tiles.append(tile)
            self.tiles.append(row_tiles)
        
        # Bottom menu
        self.bottom_frame = tk.Frame(self.window, bg="#bbada0")
        self.bottom_frame.pack(fill="x", side="bottom", padx=20, pady=20)
        
        self.save_button = tk.Button(self.bottom_frame, text="Save Game", 
                                    command=self.save_game, font=("Press Start 2P", 10),
                                    bg="#8f7a66", fg="#ffffff")
        self.save_button.pack(side="left", padx=10)
        
        self.help_button = tk.Button(self.bottom_frame, text="Help", 
                                    command=self.show_help, font=("Press Start 2P", 10),
                                    bg="#8f7a66", fg="#ffffff")
        self.help_button.pack(side="left", padx=10)
        
        self.quit_button = tk.Button(self.bottom_frame, text="Quit", 
                                    command=self.quit_game, font=("Press Start 2P", 10),
                                    bg="#8f7a66", fg="#ffffff")
        self.quit_button.pack(side="right", padx=10)
        
        # Music control
        self.music_button = tk.Button(self.bottom_frame, text="🔊", 
                                     command=self.toggle_music, font=("Press Start 2P", 10),
                                     bg="#8f7a66", fg="#ffffff", width=2)
        self.music_button.pack(side="right", padx=10)
        
    def update_ui(self):
        """Update the UI with current grid values, using images instead of text"""
        # Precise measurements for grid alignment
        # These values are carefully tuned to match the grid background
        tile_size = 72  # Updated to match the tile size in init_ui
        
        for i in range(4):
            for j in range(4):
                value = self.grid[i, j]
                if value == 0:
                    # Make empty tiles completely invisible
                    self.tiles[i][j].place_forget()  # Remove from view
                else:
                    # Use the pre-defined positions for precise placement
                    x_pos, y_pos = self.grid_positions[i][j]
                    
                    # Make sure the tile is visible and properly placed
                    self.tiles[i][j].place(x=x_pos, y=y_pos, width=tile_size, height=tile_size)
                    
                    if value in self.images:
                        # Display the image for this value
                        self.tiles[i][j].config(image=self.images[value], text="", bg=self.colors.get(value, "#cdc1b4"))
                    else:
                        # Fallback to text if image not available
                        self.tiles[i][j].config(image="", text=str(value) if value else "", font=("Press Start 2P", 16), bg=self.colors.get(value, "#cdc1b4"))
        
        # Update score display
        self.score_label.config(text=f"Score: {self.current_score}")
        self.high_score_label.config(text=f"Best: {self.high_score}")
        
        self.window.update_idletasks()

    def spawn_tile(self, animate=True):
        empty_cells = [(r, c) for r in range(4) for c in range(4) if self.grid[r, c] == 0]
        if empty_cells:
            r, c = random.choice(empty_cells)
            value = 2 if random.random() < 0.9 else 4
            self.grid[r, c] = value
            
            if animate:
                self.animate_spawn(r, c, value)
    
    def animate_spawn(self, row, col, value):
        """Animate a new tile spawning with a retro pixel-like fade in"""
        if not hasattr(self, 'tiles') or row >= len(self.tiles) or col >= len(self.tiles[0]):
            return
            
        tile = self.tiles[row][col]
        x_pos, y_pos = self.grid_positions[row][col]
        tile_size = 72
        
        # Configure the tile with the correct image/value
        if value in self.images:
            tile.config(image=self.images[value], text="", bg=self.colors.get(value, "#cdc1b4"))
        else:
            tile.config(image="", text=str(value), bg=self.colors.get(value, "#cdc1b4"))
        
        # Start with a small tile
        start_size = 10
        tile.place(x=x_pos + (tile_size - start_size) // 2, 
                  y=y_pos + (tile_size - start_size) // 2, 
                  width=start_size, height=start_size)
        
        # Animate the growth
        def grow_tile(current_size, step=0):
            if step >= 5:  # 5 frames for the grow animation
                # Final position and size
                tile.place(x=x_pos, y=y_pos, width=tile_size, height=tile_size)
                return
            
            # Calculate new size with a retro step-like growth (not smooth)
            new_size = start_size + (tile_size - start_size) * (step + 1) // 5
            
            # Update position to keep centered
            new_x = x_pos + (tile_size - new_size) // 2
            new_y = y_pos + (tile_size - new_size) // 2
            
            tile.place(x=new_x, y=new_y, width=new_size, height=new_size)
            
            # Schedule next frame
            self.window.after(30, grow_tile, new_size, step + 1)
        
        # Start the animation
        grow_tile(start_size)
    
    def move(self, direction):
        """Handle tile movement in the specified direction"""
        if self.is_animating:
            return  # Don't process moves during animation
            
        # Store the original grid for comparison and animation
        original_grid = self.grid.copy()
        self.last_grid = original_grid.copy()
        
        # Process the move logic based on direction
        moved = False
        merged_positions = []
        
        if direction == 'up':
            # Transpose to work with columns as rows
            self.grid = self.grid.T
            for i in range(4):
                result, merged = self.process_row(self.grid[i])
                if result:
                    moved = True
                    merged_positions.extend([(pos, i) for pos in merged])
            # Transpose back
            self.grid = self.grid.T
            # Correct merged positions after transposition
            merged_positions = [(col, row) for row, col in merged_positions]
            
        elif direction == 'down':
            # Transpose to work with columns as rows
            self.grid = self.grid.T
            for i in range(4):
                # Reverse the row, process it, then reverse back
                row = self.grid[i][::-1]
                result, merged = self.process_row(row)
                if result:
                    moved = True
                    # Adjust positions for reversed row (3-pos for 0-based indexing)
                    merged_positions.extend([(3 - pos, i) for pos in merged])
                # Put the processed row back in the grid (reversed again)
                self.grid[i] = row[::-1]
            # Transpose back
            self.grid = self.grid.T
            # Correct merged positions after transposition
            merged_positions = [(col, row) for row, col in merged_positions]
            
        elif direction == 'left':
            for i in range(4):
                result, merged = self.process_row(self.grid[i])
                if result:
                    moved = True
                    merged_positions.extend([(i, pos) for pos in merged])
                    
        elif direction == 'right':
            for i in range(4):
                # Reverse the row, process it, then reverse back
                row = self.grid[i][::-1]
                result, merged = self.process_row(row)
                if result:
                    moved = True
                    # Adjust positions for reversed row
                    merged_positions.extend([(i, 3 - pos) for pos in merged])
                # Put the processed row back in the grid (reversed again)
                self.grid[i] = row[::-1]
        
        # Check if the grid changed
        if moved:
            self.play_sound('move')
            
            # Find differences between old and new grid for animation
            movements = self.calculate_movements(original_grid, self.grid)
            
            # Animate the movements
            self.animate_grid_change(movements, merged_positions, direction)
            
            # Spawn a new tile after movement
            self.spawn_tile()
            
            # Update high score if current score is higher
            if self.current_score > self.high_score:
                self.high_score = self.current_score
                self.save_high_score()
            
            # Check if game is over
            if self.is_game_over():
                self.play_sound('game_over')
                self.show_game_over()
        else:
            # If grid didn't change, ensure UI is still updated
            self.update_ui()
    
    def process_row(self, row):
        """Process a single row for movement and merging"""
        original = row.copy()
        # First compression
        row_compressed = self.compress(row)
        # Merge
        row_merged, merged_positions = self.merge_with_tracking(row_compressed)
        # Second compression
        row_final = self.compress(row_merged)
        
        # Update the row in place
        row[:] = row_final
        
        # Return whether the row changed and merged positions
        return not np.array_equal(original, row_final), merged_positions
    
    def calculate_movements(self, old_grid, new_grid):
        """Calculate tile movements between old and new grid states"""
        movements = []
        
        # Create dictionaries of values and their positions in old and new grids
        old_positions = {}
        for i in range(4):
            for j in range(4):
                if old_grid[i, j] != 0:
                    value = old_grid[i, j]
                    if value not in old_positions:
                        old_positions[value] = []
                    old_positions[value].append((i, j))
        
        new_positions = {}
        for i in range(4):
            for j in range(4):
                if new_grid[i, j] != 0:
                    value = new_grid[i, j]
                    if value not in new_positions:
                        new_positions[value] = []
                    new_positions[value].append((i, j))
        
        # Match tiles from old to new positions
        for value in old_positions:
            if value in new_positions:
                # Simple case: same number of tiles with this value
                if len(old_positions[value]) == len(new_positions[value]):
                    # For simplicity, match old and new positions in order
                    # This isn't perfect but works for most cases
                    for old_pos, new_pos in zip(old_positions[value], new_positions[value]):
                        if old_pos != new_pos:  # Only track actual movements
                            movements.append((old_pos, new_pos))
                else:
                    # More complex case: tiles merged or new tiles appeared
                    # Match as many as possible
                    for old_pos in old_positions[value]:
                        if new_positions[value]:  # If there are still new positions available
                            new_pos = new_positions[value].pop(0)
                            if old_pos != new_pos:  # Only track actual movements
                                movements.append((old_pos, new_pos))
        
        return movements
    
    def animate_grid_change(self, movements, merged_positions, direction):
        """Animate the entire grid change including movements and merges"""
        self.is_animating = True
        tile_size = 72
        
        # If no movements, skip directly to spawning a tile
        if not movements:
            self.spawn_tile()
            self.update_ui()
            self.is_animating = False
            return
        
        # Hide all tiles initially - we'll show them in their animated positions
        for i in range(4):
            for j in range(4):
                self.tiles[i][j].place_forget()
        
        # Create temporary labels for moving tiles
        temp_tiles = []
        
        # Create a temporary label for each movement
        for (src_row, src_col), (dst_row, dst_col) in movements:
            if self.last_grid[src_row, src_col] == 0:
                continue  # Skip empty tiles
                
            # Get the value from the original grid
            value = self.last_grid[src_row, src_col]
            
            # Create a temporary tile for animation
            temp_tile = tk.Label(self.frame, font=("Press Start 2P", 16), 
                              compound="center", borderwidth=0, highlightthickness=0)
            
            # Configure with image or text
            if value in self.images:
                temp_tile.config(image=self.images[value], text="", bg=self.colors.get(value, "#cdc1b4"))
            else:
                temp_tile.config(image="", text=str(value), bg=self.colors.get(value, "#cdc1b4"))
            
            # Position at source
            src_x, src_y = self.grid_positions[src_row][src_col]
            temp_tile.place(x=src_x, y=src_y, width=tile_size, height=tile_size)
            
            # Calculate destination
            dst_x, dst_y = self.grid_positions[dst_row][dst_col]
            
            # Store for animation
            temp_tiles.append((temp_tile, src_x, src_y, dst_x, dst_y, dst_row, dst_col))
        
        # Function to update positions for one frame
        def update_positions(step):
            if step >= 8:  # 8 frames for movement (retro-style step animation)
                # Animation complete, clean up
                for temp_tile, _, _, _, _, _, _ in temp_tiles:
                    temp_tile.destroy()
                
                # Spawn a new tile and update UI
                self.spawn_tile()
                
                # Force a full UI update to ensure all tiles are properly visible
                self.update_ui()
                
                # Animate merges
                if merged_positions:
                    self.animate_merges(merged_positions)
                else:
                    # No merges to animate, so we're done
                    self.is_animating = False
                return
            
            # Update position of each temporary tile
            for temp_tile, src_x, src_y, dst_x, dst_y, _, _ in temp_tiles:
                # Calculate new position with a retro step-like movement
                progress = (step + 1) / 8
                
                # Use step function for retro feel (not smooth)
                new_x = src_x + int((dst_x - src_x) * progress)
                new_y = src_y + int((dst_y - src_y) * progress)
                
                # Apply pixelated movement effect by rounding to nearest multiple of 4
                new_x = (new_x // 4) * 4
                new_y = (new_y // 4) * 4
                
                temp_tile.place(x=new_x, y=new_y, width=tile_size, height=tile_size)
            
            # Schedule next frame
            self.window.after(20, update_positions, step + 1)
        
        # Start the animation
        update_positions(0)
    
    def animate_merges(self, merged_positions):
        """Animate tile merges with a retro popping effect"""
        if not merged_positions:
            self.is_animating = False
            return
            
        tile_size = 72
        
        # Count for tracking when all animations are complete
        self.merge_animations_count = len(merged_positions)
        self.completed_merge_animations = 0
        
        # For each merged tile position
        for row, col in merged_positions:
            if row >= len(self.tiles) or col >= len(self.tiles[0]):
                self.completed_merge_animations += 1
                continue
                
            tile = self.tiles[row][col]
            value = self.grid[row, col]
            
            if value == 0:
                self.completed_merge_animations += 1
                continue
                
            x_pos, y_pos = self.grid_positions[row][col]
            
            # Configure with correct image/value
            if value in self.images:
                tile.config(image=self.images[value], text="", bg=self.colors.get(value, "#cdc1b4"))
            else:
                tile.config(image="", text=str(value), bg=self.colors.get(value, "#cdc1b4"))
            
            # Make sure the tile is visible
            tile.place(x=x_pos, y=y_pos, width=tile_size, height=tile_size)
            
            # Play merge sound
            self.play_sound('merge')
            
            # Animate the merge with a pop effect
            def pop_effect(tile, step=0):
                if step >= 6:  # 6 frames for pop animation
                    # Reset to normal size
                    tile.place(x=x_pos, y=y_pos, width=tile_size, height=tile_size)
                    
                    # Increment completed animations counter
                    self.completed_merge_animations += 1
                    
                    # Check if this was the last animation
                    if self.completed_merge_animations >= self.merge_animations_count:
                        self.is_animating = False
                        # One final UI update to ensure everything is visible
                        self.update_ui()
                    return
                
                # Pop effect: grow slightly then shrink back
                if step < 3:
                    # Growing phase
                    scale = 1.0 + (step + 1) * 0.1  # Grow up to 30% larger
                else:
                    # Shrinking phase
                    scale = 1.3 - (step - 2) * 0.1  # Shrink back to normal
                
                # Calculate new size and position
                new_size = int(tile_size * scale)
                new_x = x_pos - (new_size - tile_size) // 2
                new_y = y_pos - (new_size - tile_size) // 2
                
                # Update tile
                tile.place(x=new_x, y=new_y, width=new_size, height=new_size)
                
                # Schedule next frame
                self.window.after(30, pop_effect, tile, step + 1)
            
            # Start the animation
            pop_effect(tile)
        
        # If no valid animations were started, reset the flag
        if self.completed_merge_animations >= self.merge_animations_count:
            self.is_animating = False
            # One final UI update to ensure everything is visible
            self.update_ui()
    
    def handle_keypress(self, event):
        """Handle keyboard input for game controls"""
        if self.is_animating:
            return  # Ignore keypresses during animation
        
        key = event.keysym.lower()  # Convert to lowercase for case-insensitive matching
        
        # Movement controls
        if key in ("up", "w", "k"):  # Added 'k' for vim-style controls
            self.move('up')
        elif key in ("down", "s", "j"):  # Added 'j' for vim-style controls
            self.move('down')
        elif key in ("left", "a", "h"):  # Added 'h' for vim-style controls
            self.move('left')
        elif key in ("right", "d", "l"):  # Added 'l' for vim-style controls
            self.move('right')
        
        # Game controls
        elif key == "r":  # Restart game
            self.restart_game()
        elif key == "q":  # Quit game
            self.quit_game()
        elif key == "m":  # Toggle music/sound
            self.toggle_music()
        elif key == "h":  # Show help
            self.show_help()
        elif key == "f1":  # Alternative help key
            self.show_help()
        elif key == "escape":  # Show menu/pause
            self.show_menu()
    
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
        # Check if sound exists and is enabled
        if sound_key in self.sounds and self.sounds[sound_key] is not None:
            # Only check music_on if it exists, otherwise default to playing sound
            if not hasattr(self, 'music_on') or self.music_on:
                try:
                    self.sounds[sound_key].play()
                except Exception as e:
                    print(f"Error playing sound {sound_key}: {e}")
    
    def load_grid_background(self):
        """Load grid background image"""
        # Path to images folder - create if it doesn't exist
        image_folder = os.path.join(os.path.dirname(__file__), "images")
        os.makedirs(image_folder, exist_ok=True)
        
        bg_path = os.path.join(image_folder, "grid_background.png")
        if not os.path.exists(bg_path):
            try:
                # Create a basic grid background if one doesn't exist
                bg_img = Image.new('RGBA', (400, 400), (187, 173, 160, 255))  # Main grid background color
                
                # Draw grid cells
                for i in range(4):
                    for j in range(4):
                        # Create a rounded rectangle for each cell
                        cell = Image.new('RGBA', (72, 72), (205, 193, 180, 255))  # Empty cell color
                        bg_img.paste(cell, (j*92+25, i*92+25), mask=None)
                
                bg_img.save(bg_path)
                print(f"Created grid background image at: {bg_path}")
            except Exception as e:
                print(f"Error creating grid background: {e}")
                self.grid_background = None
                return
        
        try:
            # Open the image and apply zoom effect by cropping and resizing
            img = Image.open(bg_path)
            
            # Get original dimensions
            width, height = img.size
            
            # Calculate zoom factor (5% zoom)
            zoom_factor = 1.05
            
            # Calculate new dimensions for cropping
            new_width = int(width / zoom_factor)
            new_height = int(height / zoom_factor)
            
            # Calculate crop box (centered)
            left = (width - new_width) // 2
            top = (height - new_height) // 2
            right = left + new_width
            bottom = top + new_height
            
            # Crop the image to zoom in
            img = img.crop((left, top, right, bottom))
            
            # Resize back to original dimensions
            img = img.resize((400, 400), Image.Resampling.LANCZOS)
            
            self.grid_background = ImageTk.PhotoImage(img)
            print("Successfully loaded grid background image with zoom effect")
        except Exception as e:
            print(f"Error loading grid background: {e}")
            self.grid_background = None
    
    def load_custom_fonts(self):
        """Load and register custom fonts for the game"""
        font_path = os.path.join(os.path.dirname(__file__), "fonts", "PressStart2P.ttf")
        if os.path.exists(font_path):
            try:
                # Register the font with Tkinter
                font_id = tkFont.Font(font=("TkDefaultFont", 10)).actual()["family"]
                if "Press Start 2P" not in tkFont.families():
                    tkFont.families()  # Initialize the font system
                    self.window.tk.call('font', 'configure', font_id, '-family', "Press Start 2P")
                    self.window.tk.call('lappend', 'auto_path', os.path.join(os.path.dirname(__file__), "fonts"))
                    self.window.tk.call('lappend', 'auto_path', os.path.dirname(__file__))
                    self.window.tk.call('font', 'create', "Press Start 2P")
                    print("Custom font loaded successfully")
            except Exception as e:
                print(f"Error loading custom font: {e}")
        else:
            print(f"Font file not found: {font_path}")
    
    def load_images(self):
        """Load all tile images from the images folder"""
        # Path to images folder - create if it doesn't exist
        image_folder = os.path.join(os.path.dirname(__file__), "images")
        os.makedirs(image_folder, exist_ok=True)
        
        # Define the tile size to match our UI
        tile_size = 72  # Updated to match the tile size in init_ui
        
        # Create empty tile image if it doesn't exist
        empty_tile_path = os.path.join(image_folder, "empty.png")
        if not os.path.exists(empty_tile_path):
            try:
                # Create a blank transparent image for empty tiles
                empty_img = Image.new('RGBA', (tile_size, tile_size), (205, 193, 180, 255))
                empty_img.save(empty_tile_path)
                print(f"Created empty tile image at: {empty_tile_path}")
            except Exception as e:
                print(f"Error creating empty tile image: {e}")
        
        # Load the empty tile image
        try:
            img = Image.open(empty_tile_path)
            img = img.resize((tile_size, tile_size), Image.Resampling.LANCZOS)
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
                    img = img.resize((tile_size, tile_size), Image.Resampling.LANCZOS)
                    photo_img = ImageTk.PhotoImage(img)
                    self.images[value] = photo_img  # Store the PhotoImage
                    print(f"Successfully loaded image for tile {value}")
                except Exception as e:
                    print(f"Error loading image for tile {value}: {e}")
            else:
                print(f"Image file not found: {image_path}")
    
    def compress(self, row):
        # Fix: NumPy arrays don't have count() method
        # Convert row to list, count zeros, then create new row
        row_list = list(row)
        zero_count = row_list.count(0)
        new_row = [num for num in row_list if num != 0] + [0] * zero_count
        return np.array(new_row)
    
    def merge_with_tracking(self, row):
        """Modified merge function that tracks which positions had merges"""
        merged_positions = []
        for i in range(3):
            if row[i] == row[i+1] and row[i] != 0:
                row[i] *= 2
                row[i+1] = 0
                self.current_score += row[i]  # Update score when tiles merge
                merged_positions.append(i)  # Track the position where merge happened
                if row[i] == 2048:
                    self.show_win_message()
                self.play_sound('merge')
        return row, merged_positions
    
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
        self.is_animating = False  # Reset animation flag
        self.spawn_tile(animate=False)
        self.spawn_tile(animate=False)
        self.update_ui()
    
    def save_game(self):
        """Save the current game state"""
        # Don't save during animation
        if self.is_animating:
            return
            
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
            self.is_animating = False  # Reset animation flag
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
        """Toggle music/sound effects on/off"""
        if not hasattr(self, 'music_on'):
            self.music_on = True
        
        self.music_on = not self.music_on
        status = "ON" if self.music_on else "OFF"
        messagebox.showinfo("Sound", f"Sound effects are now {status}")
    
    def quit_game(self):
        """Exit to main menu"""
        # Don't allow quitting during animation
        if self.is_animating:
            return
            
        if messagebox.askyesno("Quit Game", "Are you sure you want to quit? Your progress will be lost unless saved."):
            self.window.destroy()
            root = tk.Tk()
            root.title("2048 Retro Game")
            root.geometry("400x600")
            MainMenu(root)
    
    def show_menu(self):
        """Show a simple in-game menu"""
        if self.is_animating:
            return
            
        menu = tk.Toplevel(self.window)
        menu.title("Game Menu")
        menu.geometry("250x300")
        menu.resizable(False, False)
        menu.configure(bg="#333333")
        
        # Center the menu on the screen
        menu.transient(self.window)
        menu.grab_set()
        
        # Title
        title_label = tk.Label(menu, text="MENU", font=("Press Start 2P", 16), 
                              fg="#FFFFFF", bg="#333333")
        title_label.pack(pady=15)
        
        # Buttons
        button_style = {"font": ("Press Start 2P", 10), "width": 15, "height": 1, 
                       "bg": "#555555", "fg": "#FFFFFF", "activebackground": "#777777"}
        
        resume_button = tk.Button(menu, text="Resume", command=menu.destroy, **button_style)
        resume_button.pack(pady=5)
        
        restart_button = tk.Button(menu, text="Restart", 
                                  command=lambda: [menu.destroy(), self.restart_game()], **button_style)
        restart_button.pack(pady=5)
        
        sound_text = "Sound: ON" if hasattr(self, 'music_on') and self.music_on else "Sound: OFF"
        sound_button = tk.Button(menu, text=sound_text, 
                               command=lambda: [menu.destroy(), self.toggle_music()], **button_style)
        sound_button.pack(pady=5)
        
        help_button = tk.Button(menu, text="Help", 
                              command=lambda: [menu.destroy(), self.show_help()], **button_style)
        help_button.pack(pady=5)
        
        save_button = tk.Button(menu, text="Save Game", 
                              command=lambda: [menu.destroy(), self.save_game()], **button_style)
        save_button.pack(pady=5)
        
        quit_button = tk.Button(menu, text="Quit", 
                              command=lambda: [menu.destroy(), self.quit_game()], **button_style)
        quit_button.pack(pady=5)

class MainMenu:
    def __init__(self, master):
        self.master = master
        self.master.title("2048 Retro Game")
        self.frame = tk.Frame(master, bg="#000000", width=400, height=600)
        self.frame.pack(fill="both", expand=True)
        
        # Load high score
        self.high_score = self.load_high_score()
        
        # Load custom fonts
        self.load_custom_fonts()
        
        # Load pixel art background if available
        self.load_background()
        
        # High Score Display
        self.high_score_label = tk.Label(self.frame, text=f"High Score: {self.high_score}", 
                                        font=("Press Start 2P", 14), fg="#FFFFFF", bg="#000000")
        self.high_score_label.pack(pady=20)
        
        # Title
        self.title_label = tk.Label(self.frame, text="2048 RETRO", 
                                   font=("Press Start 2P", 28), fg="#FFD700", bg="#000000")
        self.title_label.pack(pady=20)
        
        # Main Menu Buttons
        button_frame = tk.Frame(self.frame, bg="#000000")
        button_frame.pack(pady=20)
        
        button_style = {"font": ("Press Start 2P", 12), "width": 15, "height": 2, 
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
    
    def load_custom_fonts(self):
        """Load and register custom fonts for the menu"""
        font_path = os.path.join(os.path.dirname(__file__), "fonts", "PressStart2P.ttf")
        if os.path.exists(font_path):
            try:
                # Register the font with Tkinter
                font_id = tkFont.Font(font=("TkDefaultFont", 10)).actual()["family"]
                if "Press Start 2P" not in tkFont.families():
                    tkFont.families()  # Initialize the font system
                    self.master.tk.call('font', 'configure', font_id, '-family', "Press Start 2P")
                    self.master.tk.call('lappend', 'auto_path', os.path.join(os.path.dirname(__file__), "fonts"))
                    self.master.tk.call('lappend', 'auto_path', os.path.dirname(__file__))
                    self.master.tk.call('font', 'create', "Press Start 2P")
                    print("Custom font loaded successfully")
            except Exception as e:
                print(f"Error loading custom font: {e}")
        else:
            print(f"Font file not found: {font_path}")
    
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
