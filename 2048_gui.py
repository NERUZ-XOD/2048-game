import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import numpy as np
import random
import os
import json
import pygame
from tkinter import messagebox
import tkinter.font as tkFont
import time
import sys

class Game2048:
    def __init__(self, master):
        self.window = master
        self.window.title("2048 Retro Game")
        self.window.geometry("400x600")
        self.window.resizable(False, False)  # Disable resizing
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
        
        # Original grid positions (for windowed mode)
        self.original_grid_positions = [
            # Row 1
            [(25, 25), (117, 25), (209, 25), (301, 25)],
            # Row 2
            [(25, 117), (117, 117), (209, 117), (301, 117)],
            # Row 3
            [(25, 209), (117, 209), (209, 209), (301, 209)],
            # Row 4
            [(25, 301), (117, 301), (209, 301), (301, 301)]
        ]
        
        # Current grid positions (may be scaled in fullscreen)
        self.grid_positions = [row[:] for row in self.original_grid_positions]
        
        # Base tile size (for windowed mode)
        self.base_tile_size = 72
        self.current_tile_size = self.base_tile_size
        
        # Load tile images and grid background before UI initialization
        self.images = {}
        self.load_background_image()  
        self.load_grid_background()
        self.load_images()
        
        # Initialize UI components
        self.init_ui()
        
        self.spawn_tile(animate=False)
        self.spawn_tile(animate=False)
        self.update_ui()

        self.window.bind("<Key>", self.handle_keypress)
    
    def init_ui(self):
        """Initialize the UI components"""
        # Create a background frame that covers the entire window
        self.bg_frame = tk.Frame(self.window, bg="#000000")
        self.bg_frame.place(x=0, y=0, relwidth=1, relheight=1)
        
        # If we have a background image, display it
        if hasattr(self, 'background_image') and self.background_image:
            self.bg_label = tk.Label(self.bg_frame, image=self.background_image)
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Main frame for the game grid
        self.frame = tk.Frame(self.window, bg=self.empty_color, width=400, height=400)
        self.frame.pack(pady=20)
        
        # Set minimum size for the window
        self.window.minsize(400, 600)
        
        # Create a canvas for the grid background
        self.canvas = tk.Canvas(self.frame, width=400, height=400, bg=self.empty_color, 
                               highlightthickness=0)
        self.canvas.pack()
        
        # Display the grid background image
        if hasattr(self, 'grid_background') and self.grid_background:
            self.canvas.create_image(0, 0, anchor="nw", image=self.grid_background)
        
        # Score frame with semi-transparent background and neon styling
        self.score_frame = tk.Frame(self.window, bg="#222233")
        self.score_frame.pack(fill="x", padx=20, pady=10)
        
        # Add a neon border to the score frame
        score_canvas = tk.Canvas(self.score_frame, bg="#222233", height=40, highlightthickness=0)
        score_canvas.pack(fill="x", expand=True)
        score_canvas.create_rectangle(2, 2, 398, 38, outline="#00FFFF", width=2)
        
        # Score labels with neon styling
        self.score_label = tk.Label(score_canvas, text=f"Score: {self.current_score}", 
                                   font=("Press Start 2P", 12), bg="#222233", fg="#00FFFF")
        self.score_label.place(relx=0.25, rely=0.5, anchor="center")
        
        self.high_score_label = tk.Label(score_canvas, text=f"Best: {self.high_score}", 
                                        font=("Press Start 2P", 12), bg="#222233", fg="#FF00FF")
        self.high_score_label.place(relx=0.75, rely=0.5, anchor="center")
        
        # Create tile labels with consistent size
        self.tiles = []
        
        for i in range(4):
            row_tiles = []
            for j in range(4):
                # Create tile labels that will overlay on the grid
                tile = tk.Label(self.frame, text="", font=("Press Start 2P", 16), 
                              bg=self.empty_color, compound="center",
                              width=4, height=2, borderwidth=0, highlightthickness=0)
                
                # Use the pre-defined positions for precise placement
                x_pos, y_pos = self.grid_positions[i][j]
                
                tile.place(x=x_pos, y=y_pos, width=self.current_tile_size, height=self.current_tile_size)
                row_tiles.append(tile)
            self.tiles.append(row_tiles)
        
        # Bottom menu with cyberpunk styling
        self.bottom_frame = tk.Frame(self.window, bg="#000000")
        self.bottom_frame.pack(fill="x", side="bottom", padx=20, pady=20)
        
        # Create neon-styled buttons
        button_style = {
            "font": ("Press Start 2P", 10),
            "bg": "#222233",
            "activebackground": "#333344",
            "relief": tk.FLAT,
            "borderwidth": 2
        }
        
        # Save Game button with cyan styling
        self.save_button = tk.Button(self.bottom_frame, text="Save Game", 
                                    command=self.save_game, fg="#00FFFF",
                                    activeforeground="#00FFFF",
                                    highlightbackground="#00FFFF",
                                    highlightcolor="#00FFFF",
                                    highlightthickness=2,
                                    **button_style)
        self.save_button.pack(side="left", padx=10)
        
        # Help button with yellow styling
        self.help_button = tk.Button(self.bottom_frame, text="Help", 
                                    command=self.show_help, fg="#FFFF00",
                                    activeforeground="#FFFF00",
                                    highlightbackground="#FFFF00",
                                    highlightcolor="#FFFF00",
                                    highlightthickness=2,
                                    **button_style)
        self.help_button.pack(side="left", padx=10)
        
        # Quit button with red styling
        self.quit_button = tk.Button(self.bottom_frame, text="Quit", 
                                    command=self.quit_game, fg="#FF5555",
                                    activeforeground="#FF5555",
                                    highlightbackground="#FF5555",
                                    highlightcolor="#FF5555",
                                    highlightthickness=2,
                                    **button_style)
        self.quit_button.pack(side="left", padx=10)
        
        # Music toggle button with magenta styling
        self.music_button = tk.Button(self.bottom_frame, text="🔊", 
                                     command=self.toggle_music, fg="#FF00FF",
                                     activeforeground="#FF00FF",
                                     highlightbackground="#FF00FF",
                                     highlightcolor="#FF00FF",
                                     highlightthickness=2,
                                     width=2, **button_style)
        self.music_button.pack(side="right", padx=10)
    
    def update_ui(self):
        """Update the UI with current grid values, using images instead of text"""
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
                    self.tiles[i][j].place(x=x_pos, y=y_pos, width=self.current_tile_size, height=self.current_tile_size)
                    
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
        tile_size = self.current_tile_size
        
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
            self.window.after(self.animation_duration + 50, self.check_game_over)
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
        tile_size = self.current_tile_size
        
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
            
        tile_size = self.current_tile_size
        
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
        elif key == "f11" or key == "f":  # Toggle fullscreen
            pass
    
    def load_high_score(self):
        """Load high score from file"""
        try:
            # Use a more robust path that works in both script and executable modes
            app_data_dir = self.get_app_data_dir()
            high_score_path = os.path.join(app_data_dir, 'high_score.json')
            
            if os.path.exists(high_score_path):
                with open(high_score_path, 'r') as f:
                    data = json.load(f)
                    return data.get('high_score', 0)
            return 0
        except (FileNotFoundError, json.JSONDecodeError):
            return 0
    
    def save_high_score(self):
        """Save high score to file"""
        try:
            # Use a more robust path that works in both script and executable modes
            app_data_dir = self.get_app_data_dir()
            high_score_path = os.path.join(app_data_dir, 'high_score.json')
            
            # Ensure directory exists
            os.makedirs(app_data_dir, exist_ok=True)
            
            with open(high_score_path, 'w') as f:
                json.dump({'high_score': int(self.high_score)}, f)
        except Exception as e:
            print(f"Error saving high score: {e}")
    
    def get_app_data_dir(self):
        """Get a consistent directory for app data that works in both script and executable modes"""
        # For Windows, use AppData folder
        app_name = "2048Game"
        if hasattr(sys, 'frozen'):
            # Running as compiled executable
            base_dir = os.path.dirname(sys.executable)
        else:
            # Running as script
            base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Create a data directory in the same location as the executable/script
        data_dir = os.path.join(base_dir, 'data')
        return data_dir
    
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
        tile_size = self.current_tile_size
        
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
    
    def load_background_image(self):
        """Load or create a colorful background image for the game"""
        # Path to images folder - create if it doesn't exist
        image_folder = os.path.join(os.path.dirname(__file__), "images")
        os.makedirs(image_folder, exist_ok=True)
        
        bg_path = os.path.join(image_folder, "background.png")
        if not os.path.exists(bg_path):
            try:
                # Create a colorful gradient background if one doesn't exist
                width, height = 400, 600
                
                # Create a new image with gradient
                bg_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                draw = ImageDraw.Draw(bg_img)
                
                # Create a colorful gradient background
                for y in range(height):
                    # Calculate gradient colors
                    r = int(255 * (1 - y / height) + 100 * (y / height))  # Red to purple
                    g = int(100 * (1 - y / height) + 50 * (y / height))   # Less green
                    b = int(150 * (1 - y / height) + 200 * (y / height))  # More blue at bottom
                    
                    # Draw a horizontal line with the calculated color
                    draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
                
                # Add some retro-style decorations
                # Add grid lines
                for i in range(0, width, 20):
                    alpha = 30  # Subtle transparency
                    draw.line([(i, 0), (i, height)], fill=(255, 255, 255, alpha), width=1)
                
                for i in range(0, height, 20):
                    alpha = 30  # Subtle transparency
                    draw.line([(0, i), (width, i)], fill=(255, 255, 255, alpha), width=1)
                
                # Add some random pixels for a retro effect
                for _ in range(300):
                    x = random.randint(0, width-1)
                    y = random.randint(0, height-1)
                    size = random.randint(1, 3)
                    alpha = random.randint(30, 100)
                    color = (255, 255, 255, alpha)
                    draw.rectangle([x, y, x+size, y+size], fill=color)
                
                # Save the background
                bg_img.save(bg_path)
                print(f"Created background image at: {bg_path}")
            except Exception as e:
                print(f"Error creating background image: {e}")
                self.background_image = None
                return
        
        try:
            # Load the background image
            img = Image.open(bg_path)
            self.background_image = ImageTk.PhotoImage(img)
            print("Successfully loaded background image")
        except Exception as e:
            print(f"Error loading background image: {e}")
            self.background_image = None
    
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
                # Removing duplicate sound trigger - the animate_merges method already plays this sound
                # self.play_sound('merge')
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
    
    def check_game_over(self):
        """Check if the game is over after animation completes"""
        # Reset animation flag to ensure game over screen can be shown
        self.is_animating = False
        
        # Check if game is over
        if self.is_game_over():
            self.show_game_over()
    
    def show_game_over(self):
        """Show game over message with retro styling"""
        print("Game over detected, showing game over screen")
        
        # Don't show game over during animation
        if self.is_animating:
            print("Animation in progress, not showing game over screen")
            return
            
        # Play game over sound
        self.play_sound('game_over')
        
        # Create a new top-level window
        game_over = tk.Toplevel()
        game_over.title("Game Over")
        game_over.geometry("400x600")
        game_over.resizable(False, False)
        game_over.configure(bg="#000000")
        
        # Ensure it stays on top
        game_over.attributes("-topmost", True)
        
        # Load background image
        try:
            bg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "menu_background.png")
            if os.path.exists(bg_path):
                img = Image.open(bg_path)
                img = img.resize((400, 600), Image.Resampling.LANCZOS)
                bg_image = ImageTk.PhotoImage(img)
                
                # Create background label
                bg_label = tk.Label(game_over, image=bg_image)
                bg_label.image = bg_image  # Keep a reference to prevent garbage collection
                bg_label.place(x=0, y=0, relwidth=1, relheight=1)
                print("Successfully loaded game over background image")
        except Exception as e:
            print(f"Error loading background for game over: {e}")
        
        # Create a semi-transparent frame for content
        content_frame = tk.Frame(game_over, bg="#000000")
        content_frame.place(relx=0.5, rely=0.5, anchor="center", width=300, height=400)
        
        # Add a red border around the frame
        border_frame = tk.Frame(game_over, bg="#FF0000")
        border_frame.place(relx=0.5, rely=0.5, anchor="center", width=304, height=404)
        content_frame.lift()  # Bring content frame to front
        
        # Game Over title
        title_label = tk.Label(content_frame, text="GAME OVER", 
                              font=("Press Start 2P", 24), fg="#FF0000", bg="#000000")
        title_label.pack(pady=(20, 10))
        
        # Add a separator line
        separator = tk.Canvas(content_frame, width=250, height=2, bg="#000000",
                            highlightthickness=0)
        separator.pack(pady=10)
        separator.create_line(0, 1, 250, 1, fill="#FF0000", width=2)
        
        # Score display
        score_label = tk.Label(content_frame, text=f"SCORE: {self.current_score}", 
                             font=("Press Start 2P", 16), fg="#FFFF00", bg="#000000")
        score_label.pack(pady=10)
        
        # High score display
        high_score = max(self.high_score, self.current_score)
        high_score_label = tk.Label(content_frame, text=f"HIGH SCORE: {high_score}", 
                                  font=("Press Start 2P", 12), fg="#00FFFF", bg="#000000")
        high_score_label.pack(pady=5)
        
        # Add another separator line
        separator2 = tk.Canvas(content_frame, width=250, height=2, bg="#000000",
                             highlightthickness=0)
        separator2.pack(pady=15)
        separator2.create_line(0, 1, 250, 1, fill="#FF0000", width=2)
        
        # Buttons frame
        button_frame = tk.Frame(content_frame, bg="#000000")
        button_frame.pack(pady=20)
        
        # Button style
        button_style = {"font": ("Press Start 2P", 12), "width": 12, "height": 2, 
                       "bg": "#111122", "activebackground": "#222233", 
                       "relief": tk.FLAT, "borderwidth": 2}
        
        # Try again button
        restart_button = tk.Button(button_frame, text="TRY AGAIN", fg="#00FF00",
                                 command=lambda: [game_over.destroy(), self.restart_game()],
                                 **button_style)
        restart_button.pack(pady=10)
        
        # Quit button
        quit_button = tk.Button(button_frame, text="QUIT", fg="#FF5555",
                              command=lambda: [game_over.destroy(), self.quit_game()],
                              **button_style)
        quit_button.pack(pady=10)
        
        # Update high score if needed
        if self.current_score > self.high_score:
            self.high_score = self.current_score
            self.save_high_score()
        
        # Make sure the window stays on top and gets focus
        game_over.lift()
        game_over.focus_force()
    
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
            
        # Prepare game state
        game_state = {
            'grid': self.grid.tolist(),
            'score': int(self.current_score),
            'high_score': int(self.high_score)
        }
        
        try:
            # Use the same app data directory as high score
            app_data_dir = self.get_app_data_dir()
            save_path = os.path.join(app_data_dir, 'saved_game.json')
            
            # Ensure directory exists
            os.makedirs(app_data_dir, exist_ok=True)
            
            with open(save_path, 'w') as f:
                json.dump(game_state, f)
            self.show_save_success()
        except Exception as e:
            print(f"Error saving game: {e}")
            messagebox.showerror("Save Error", f"Could not save game: {e}")
    
    def show_save_success(self):
        """Show a stylized game saved success message"""
        # Create a new top-level window
        save_success = tk.Toplevel()
        save_success.title("Game Saved")
        save_success.geometry("350x250")
        save_success.resizable(False, False)
        save_success.configure(bg="#000000")
        
        # Ensure it stays on top
        save_success.attributes("-topmost", True)
        
        # Load background image
        try:
            bg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "menu_background.png")
            if os.path.exists(bg_path):
                img = Image.open(bg_path)
                img = img.resize((350, 250), Image.Resampling.LANCZOS)
                bg_image = ImageTk.PhotoImage(img)
                
                # Create background label
                bg_label = tk.Label(save_success, image=bg_image)
                bg_label.image = bg_image  # Keep a reference to prevent garbage collection
                bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as e:
            print(f"Error loading background for save success: {e}")
        
        # Create a semi-transparent frame for content
        content_frame = tk.Frame(save_success, bg="#000000")
        content_frame.place(relx=0.5, rely=0.5, anchor="center", width=300, height=200)
        
        # Add a green border around the frame (green for success)
        border_frame = tk.Frame(save_success, bg="#00FF00")
        border_frame.place(relx=0.5, rely=0.5, anchor="center", width=304, height=204)
        content_frame.lift()  # Bring content frame to front
        
        # Success title
        title_label = tk.Label(content_frame, text="GAME SAVED", 
                              font=("Press Start 2P", 18), fg="#00FF00", bg="#000000")
        title_label.pack(pady=(30, 20))
        
        # Add a separator line
        separator = tk.Canvas(content_frame, width=250, height=2, bg="#000000",
                            highlightthickness=0)
        separator.pack(pady=10)
        separator.create_line(0, 1, 250, 1, fill="#00FF00", width=2)
        
        # Success message
        message_label = tk.Label(content_frame, text="Your game has been\nsaved successfully!", 
                               font=("Press Start 2P", 10), fg="#FFFFFF", bg="#000000",
                               justify=tk.CENTER)
        message_label.pack(pady=10)
        
        # OK button
        ok_button = tk.Button(content_frame, text="OK", 
                            font=("Press Start 2P", 12), fg="#00FF00", bg="#111122",
                            width=8, height=1, command=save_success.destroy,
                            relief=tk.FLAT, borderwidth=2,
                            activebackground="#222233", activeforeground="#00FF00")
        ok_button.pack(pady=15)
        
        # Auto-close after 3 seconds
        save_success.after(3000, save_success.destroy)
    
    def load_game(self):
        """Load a saved game state"""
        try:
            # Use the same app data directory as high score
            app_data_dir = self.get_app_data_dir()
            save_path = os.path.join(app_data_dir, 'saved_game.json')
            
            if not os.path.exists(save_path):
                self.show_no_save()
                return
                
            with open(save_path, 'r') as f:
                game_state = json.load(f)
                
                # Restore grid
                self.grid = np.array(game_state['grid'])
                
                # Restore score
                self.current_score = int(game_state['score'])
                
                # Restore high score
                self.high_score = int(game_state['high_score'])
                
                # Reset animation flag
                self.is_animating = False
                
                # Update UI
                self.update_ui()
                
                # Show success message
                self.show_game_loaded()
                
                return True
                
        except (FileNotFoundError, json.JSONDecodeError):
            self.show_no_save()
            return False
        except Exception as e:
            print(f"Error loading game: {e}")
            messagebox.showerror("Load Error", f"Could not load game: {e}")
            return False
    
    def show_game_loaded(self):
        """Show a stylized game loaded success message"""
        # Create a new top-level window
        load_success = tk.Toplevel()
        load_success.title("Game Loaded")
        load_success.geometry("350x250")
        load_success.resizable(False, False)
        load_success.configure(bg="#000000")
        
        # Ensure it stays on top
        load_success.attributes("-topmost", True)
        
        # Load background image
        try:
            bg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "menu_background.png")
            if os.path.exists(bg_path):
                img = Image.open(bg_path)
                img = img.resize((350, 250), Image.Resampling.LANCZOS)
                bg_image = ImageTk.PhotoImage(img)
                
                # Create background label
                bg_label = tk.Label(load_success, image=bg_image)
                bg_label.image = bg_image  # Keep a reference to prevent garbage collection
                bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as e:
            print(f"Error loading background for load success: {e}")
        
        # Create a semi-transparent frame for content
        content_frame = tk.Frame(load_success, bg="#000000")
        content_frame.place(relx=0.5, rely=0.5, anchor="center", width=300, height=200)
        
        # Add a blue border around the frame (blue for information)
        border_frame = tk.Frame(load_success, bg="#3399FF")
        border_frame.place(relx=0.5, rely=0.5, anchor="center", width=304, height=204)
        content_frame.lift()  # Bring content frame to front
        
        # Information icon
        icon_frame = tk.Frame(content_frame, bg="#000000", width=50, height=50)
        icon_frame.pack(pady=(20, 0))
        
        # Create a circular background for the icon
        icon_canvas = tk.Canvas(icon_frame, width=50, height=50, bg="#000000", highlightthickness=0)
        icon_canvas.pack()
        icon_canvas.create_oval(5, 5, 45, 45, fill="#3399FF", outline="")
        icon_canvas.create_text(25, 25, text="i", font=("Press Start 2P", 20), fill="#FFFFFF")
        
        # Success message
        message_label = tk.Label(content_frame, text="Your saved game has been\nloaded successfully!", 
                               font=("Press Start 2P", 10), fg="#CCCCCC", bg="#000000",
                               justify=tk.CENTER)
        message_label.pack(pady=20)
        
        # OK button
        ok_button = tk.Button(content_frame, text="OK", 
                            font=("Press Start 2P", 12), fg="#FFFFFF", bg="#3399FF",
                            width=8, height=1, command=load_success.destroy,
                            relief=tk.FLAT, borderwidth=2,
                            activebackground="#4488FF", activeforeground="#FFFFFF")
        ok_button.pack(pady=15)
        
        # Auto-close after 3 seconds
        load_success.after(3000, load_success.destroy)
    
    def show_no_save(self):
        """Show a stylized no saved game found message"""
        # Create a new top-level window
        no_save = tk.Toplevel()
        no_save.title("No Saved Game")
        no_save.geometry("350x250")
        no_save.resizable(False, False)
        no_save.configure(bg="#000000")
        
        # Ensure it stays on top
        no_save.attributes("-topmost", True)
        
        # Load background image
        try:
            bg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "menu_background.png")
            if os.path.exists(bg_path):
                img = Image.open(bg_path)
                img = img.resize((350, 250), Image.Resampling.LANCZOS)
                bg_image = ImageTk.PhotoImage(img)
                
                # Create background label
                bg_label = tk.Label(no_save, image=bg_image)
                bg_label.image = bg_image  # Keep a reference to prevent garbage collection
                bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as e:
            print(f"Error loading background for no save dialog: {e}")
        
        # Create a semi-transparent frame for content
        content_frame = tk.Frame(no_save, bg="#000000")
        content_frame.place(relx=0.5, rely=0.5, anchor="center", width=300, height=200)
        
        # Add a yellow border around the frame (yellow for warning/notification)
        border_frame = tk.Frame(no_save, bg="#FFCC00")
        border_frame.place(relx=0.5, rely=0.5, anchor="center", width=304, height=204)
        content_frame.lift()  # Bring content frame to front
        
        # Information icon
        icon_frame = tk.Frame(content_frame, bg="#000000", width=50, height=50)
        icon_frame.pack(pady=(20, 0))
        
        # Create a circular background for the icon
        icon_canvas = tk.Canvas(icon_frame, width=50, height=50, bg="#000000", highlightthickness=0)
        icon_canvas.pack()
        icon_canvas.create_oval(5, 5, 45, 45, fill="#FFCC00", outline="")
        icon_canvas.create_text(25, 25, text="!", font=("Press Start 2P", 20), fill="#000000")
        
        # Message
        message_label = tk.Label(content_frame, text="No saved game found.\nStarting a new game.", 
                               font=("Press Start 2P", 10), fg="#CCCCCC", bg="#000000",
                               justify=tk.CENTER)
        message_label.pack(pady=20)
        
        # OK button
        ok_button = tk.Button(content_frame, text="OK", 
                            font=("Press Start 2P", 12), fg="#000000", bg="#FFCC00",
                            width=8, height=1, command=no_save.destroy,
                            relief=tk.FLAT, borderwidth=2,
                            activebackground="#FFD633", activeforeground="#000000")
        ok_button.pack(pady=15)
        
        # Auto-close after 3 seconds
        no_save.after(3000, no_save.destroy)
    
    def show_help(self):
        """Show help information with a custom retro-styled window"""
        # Create a new toplevel window for help
        help_window = tk.Toplevel(self.window)
        help_window.title("How to Play")
        help_window.geometry("500x450")
        help_window.resizable(False, False)
        help_window.configure(bg="#1a1a2e")
        
        # Make window modal (user must interact with it before returning to game)
        help_window.transient(self.window)
        help_window.grab_set()
        
        # Create a semi-transparent overlay for the retro look
        overlay = tk.Frame(help_window, bg="#1a1a2e", bd=0)
        overlay.place(x=0, y=0, width=500, height=450)
        
        # Create a canvas for the neon border
        border_canvas = tk.Canvas(help_window, bg="#1a1a2e", highlightthickness=0, bd=0)
        border_canvas.place(x=10, y=10, width=480, height=430)
        
        # Draw neon border with glow effect
        border_canvas.create_rectangle(2, 2, 478, 428, outline="#00FFFF", width=2)
        
        # Title with retro font
        title_label = tk.Label(help_window, text="HOW TO PLAY 2048", 
                             font=("Press Start 2P", 16), bg="#1a1a2e", fg="#FFFF00")
        title_label.pack(pady=(20, 10))
        
        # Help content frame
        content_frame = tk.Frame(help_window, bg="#1a1a2e", bd=0)
        content_frame.pack(fill="both", expand=True, padx=40, pady=10)
        
        # Game description
        desc_label = tk.Label(content_frame, text="Combine tiles with the same number\nto reach the 2048 tile!", 
                            font=("Press Start 2P", 8), bg="#1a1a2e", fg="#FFFFFF",
                            justify="center")
        desc_label.pack(pady=(0, 20))
        
        # Controls section
        controls_title = tk.Label(content_frame, text="CONTROLS", 
                                font=("Press Start 2P", 12), bg="#1a1a2e", fg="#00FFFF")
        controls_title.pack(pady=(0, 10))
        
        # Controls list
        controls = [
            ("Arrow Keys / WASD", "Move tiles"),
            ("R", "Restart game"),
            ("M", "Toggle sound"),
            ("ESC", "Show menu"),
            ("S", "Save game")
        ]
        
        # Create a frame for the controls grid
        controls_frame = tk.Frame(content_frame, bg="#1a1a2e")
        controls_frame.pack(pady=10)
        
        # Add each control with its description
        for i, (key, action) in enumerate(controls):
            key_label = tk.Label(controls_frame, text=key, 
                               font=("Press Start 2P", 8), bg="#1a1a2e", fg="#FFFF00",
                               anchor="e", width=20)
            key_label.grid(row=i, column=0, padx=(0, 10), pady=5, sticky="e")
            
            action_label = tk.Label(controls_frame, text=action, 
                                  font=("Press Start 2P", 8), bg="#1a1a2e", fg="#FFFFFF",
                                  anchor="w", width=15)
            action_label.grid(row=i, column=1, padx=(10, 0), pady=5, sticky="w")
        
        # Tips section
        tip_label = tk.Label(content_frame, text="TIP: Plan your moves carefully!\nDon't get stuck with no valid moves.", 
                           font=("Press Start 2P", 8), bg="#1a1a2e", fg="#FF9900",
                           justify="center")
        tip_label.pack(pady=20)
        
        # OK button with retro styling
        button_style = {
            "font": ("Press Start 2P", 10),
            "bg": "#1a1a2e",
            "activebackground": "#2a2a4e",
            "bd": 0,
            "width": 10,
            "height": 2,
            "relief": tk.FLAT,
        }
        
        ok_button = tk.Button(help_window, text="OK", fg="#00FFFF",
                           command=help_window.destroy,
                           **button_style)
        ok_button.pack(pady=20)
        
        # Center the window on the screen
        help_window.update_idletasks()
        width = help_window.winfo_width()
        height = help_window.winfo_height()
        x = (help_window.winfo_screenwidth() // 2) - (width // 2)
        y = (help_window.winfo_screenheight() // 2) - (height // 2)
        help_window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Make sure the window stays on top and gets focus
        help_window.lift()
        help_window.focus_force()
    
    def toggle_music(self):
        """Toggle music/sound effects on/off with a custom retro-styled notification"""
        if not hasattr(self, 'music_on'):
            self.music_on = True
        
        self.music_on = not self.music_on
        status = "ON" if self.music_on else "OFF"
        
        # Create a new toplevel window for the notification
        sound_notify = tk.Toplevel(self.window)
        sound_notify.title("Sound")
        sound_notify.geometry("350x200")
        sound_notify.resizable(False, False)
        sound_notify.configure(bg="#1a1a2e")
        
        # Make window modal
        sound_notify.transient(self.window)
        sound_notify.grab_set()
        
        # Create a canvas for the neon border
        border_canvas = tk.Canvas(sound_notify, bg="#1a1a2e", highlightthickness=0, bd=0)
        border_canvas.place(x=10, y=10, width=330, height=180)
        
        # Draw neon border with glow effect
        border_canvas.create_rectangle(2, 2, 328, 178, outline="#00FFFF", width=2)
        
        # Sound icon
        if self.music_on:
            # Speaker icon when sound is on
            icon_canvas = tk.Canvas(sound_notify, width=50, height=50, bg="#1a1a2e", highlightthickness=0)
            icon_canvas.place(x=150, y=30)
            
            # Draw speaker icon
            icon_canvas.create_oval(10, 15, 25, 35, fill="#FFFF00", outline="#FFFF00")
            icon_canvas.create_polygon(20, 25, 35, 10, 35, 40, fill="#FFFF00", outline="#FFFF00")
            
            # Draw sound waves
            icon_canvas.create_arc(38, 15, 48, 35, start=270, extent=180, style="arc", outline="#FFFF00", width=2)
        else:
            # Muted speaker icon when sound is off
            icon_canvas = tk.Canvas(sound_notify, width=50, height=50, bg="#1a1a2e", highlightthickness=0)
            icon_canvas.place(x=150, y=30)
            
            # Draw speaker icon
            icon_canvas.create_oval(10, 15, 25, 35, fill="#FF5555", outline="#FF5555")
            icon_canvas.create_polygon(20, 25, 35, 10, 35, 40, fill="#FF5555", outline="#FF5555")
            
            # Draw X over speaker
            icon_canvas.create_line(40, 15, 50, 35, fill="#FF5555", width=2)
            icon_canvas.create_line(40, 35, 50, 15, fill="#FF5555", width=2)
        
        # Status text
        status_color = "#00FF00" if self.music_on else "#FF5555"
        status_label = tk.Label(sound_notify, text=f"SOUND: {status}", 
                              font=("Press Start 2P", 12), bg="#1a1a2e", fg=status_color)
        status_label.pack(pady=(90, 20))
        
        # Auto-close after 2 seconds
        sound_notify.after(2000, sound_notify.destroy)
        
        # Center the window on the screen
        sound_notify.update_idletasks()
        width = sound_notify.winfo_width()
        height = sound_notify.winfo_height()
        x = (sound_notify.winfo_screenwidth() // 2) - (width // 2)
        y = (sound_notify.winfo_screenheight() // 2) - (height // 2)
        sound_notify.geometry(f"{width}x{height}+{x}+{y}")
        
        # Make sure the window stays on top and gets focus
        sound_notify.lift()
        sound_notify.focus_force()
    
    def quit_game(self):
        """Exit to main menu"""
        # Don't allow quitting during animation
        if self.is_animating:
            return
            
        self.show_quit_confirmation()
    
    def show_quit_confirmation(self):
        """Show a stylized quit confirmation dialog"""
        # Create a new top-level window
        quit_dialog = tk.Toplevel()
        quit_dialog.title("Quit Game")
        quit_dialog.geometry("400x250")
        quit_dialog.resizable(False, False)
        quit_dialog.configure(bg="#000000")
        
        # Ensure it stays on top
        quit_dialog.attributes("-topmost", True)
        quit_dialog.transient(self.window)
        quit_dialog.grab_set()
        
        # Load background image
        try:
            bg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "menu_background.png")
            if os.path.exists(bg_path):
                img = Image.open(bg_path)
                img = img.resize((400, 250), Image.Resampling.LANCZOS)
                bg_image = ImageTk.PhotoImage(img)
                
                # Create background label
                bg_label = tk.Label(quit_dialog, image=bg_image)
                bg_label.image = bg_image  # Keep a reference to prevent garbage collection
                bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as e:
            print(f"Error loading background for quit dialog: {e}")
        
        # Create a semi-transparent frame for content
        content_frame = tk.Frame(quit_dialog, bg="#000000")
        content_frame.place(relx=0.5, rely=0.5, anchor="center", width=350, height=200)
        
        # Add a red border around the frame (red for warning/quit)
        border_frame = tk.Frame(quit_dialog, bg="#FF5555")
        border_frame.place(relx=0.5, rely=0.5, anchor="center", width=354, height=204)
        content_frame.lift()  # Bring content frame to front
        
        # Warning icon (question mark)
        icon_frame = tk.Frame(content_frame, bg="#000000", width=50, height=50)
        icon_frame.pack(pady=(20, 0))
        
        # Create a circular background for the icon
        icon_canvas = tk.Canvas(icon_frame, width=50, height=50, bg="#000000", highlightthickness=0)
        icon_canvas.pack()
        icon_canvas.create_oval(5, 5, 45, 45, fill="#3399FF", outline="")
        icon_canvas.create_text(25, 25, text="?", font=("Press Start 2P", 20), fill="#FFFFFF")
        
        # Warning message
        message_label = tk.Label(content_frame, 
                               text="Are you sure you want to quit?\nYour progress will be lost\nunless saved.", 
                               font=("Press Start 2P", 10), fg="#CCCCCC", bg="#000000",
                               justify=tk.CENTER)
        message_label.pack(pady=15)
        
        # Buttons frame
        button_frame = tk.Frame(content_frame, bg="#000000")
        button_frame.pack(pady=15)
        
        # Yes button
        yes_button = tk.Button(button_frame, text="YES", 
                             font=("Press Start 2P", 12), fg="#FFFFFF", bg="#3399FF",
                             width=8, height=1, 
                             command=lambda: [quit_dialog.destroy(), self.do_quit()],
                             relief=tk.FLAT, borderwidth=2,
                             activebackground="#4488FF", activeforeground="#FFFFFF")
        yes_button.pack(side=tk.LEFT, padx=10)
        
        # No button
        no_button = tk.Button(button_frame, text="NO", 
                            font=("Press Start 2P", 12), fg="#FFFFFF", bg="#666666",
                            width=8, height=1, command=quit_dialog.destroy,
                            relief=tk.FLAT, borderwidth=2,
                            activebackground="#888888", activeforeground="#FFFFFF")
        no_button.pack(side=tk.LEFT, padx=10)
    
    def do_quit(self):
        """Actually quit the game after confirmation"""
        self.window.destroy()
        root = tk.Tk()
        root.title("2048 Retro Game")
        root.geometry("400x600")
        MainMenu(root)
        root.mainloop()
    
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
        button_frame = tk.Frame(menu, bg="#333333")
        button_frame.pack(pady=20)
        
        button_style = {"font": ("Press Start 2P", 10), "width": 15, "height": 1, 
                       "bg": "#111122", "fg": "#FFFFFF", "activebackground": "#777777"}
        
        resume_button = tk.Button(button_frame, text="Resume", command=menu.destroy, **button_style)
        resume_button.pack(pady=5)
        
        restart_button = tk.Button(button_frame, text="Restart", 
                                  command=lambda: [menu.destroy(), self.restart_game()], **button_style)
        restart_button.pack(pady=5)
        
        sound_text = "Sound: ON" if hasattr(self, 'music_on') and self.music_on else "Sound: OFF"
        sound_button = tk.Button(button_frame, text=sound_text, 
                               command=lambda: [menu.destroy(), self.toggle_music()], **button_style)
        sound_button.pack(pady=5)
        
        help_button = tk.Button(button_frame, text="Help", 
                              command=lambda: [menu.destroy(), self.show_help()], **button_style)
        help_button.pack(pady=5)
        
        save_button = tk.Button(button_frame, text="Save Game", 
                              command=lambda: [menu.destroy(), self.save_game()], **button_style)
        save_button.pack(pady=5)
        
        quit_button = tk.Button(button_frame, text="Quit", 
                              command=lambda: [menu.destroy(), self.quit_game()], **button_style)
        quit_button.pack(pady=5)

class MainMenu:
    def __init__(self, master):
        self.master = master
        self.master.title("2048 Retro Game")
        
        # Create a frame for the background
        self.frame = tk.Canvas(master, width=400, height=600, highlightthickness=0)
        self.frame.pack(fill="both", expand=True)

        # Set a transparent-like effect
        self.frame.create_rectangle(0, 0, 400, 600, fill="", outline="")  # Transparent area
        
        # Load high score
        self.high_score = self.load_high_score()
        
        # Load custom fonts
        self.load_custom_fonts()
        
        # Load background image
        self.load_background()
        
        # Create a semi-transparent overlay
        overlay_width = 350
        overlay_height = 500
        overlay_x = (400 - overlay_width) // 2
        overlay_y = (600 - overlay_height) // 2
        
        # Create a neon border effect first
        self.overlay_border = self.frame.create_rectangle(
            overlay_x-2, overlay_y-2, 
            overlay_x + overlay_width+2, overlay_y + overlay_height+2, 
            fill="", outline="#00FFFF", width=2
        )
        
        # Then create the semi-transparent overlay
        self.overlay = self.frame.create_rectangle(
            overlay_x, overlay_y, 
            overlay_x + overlay_width, overlay_y + overlay_height, 
            fill="#000000", outline="", stipple="gray25"  # Semi-transparent
        )
        
        # Create a frame for content
        self.content_frame = tk.Frame(self.frame, bg="#000000")
        self.content_window = self.frame.create_window(200, 300, window=self.content_frame)
        
        # High Score Display with glow effect
        score_frame = tk.Frame(self.content_frame, bg="#000000")
        score_frame.pack(pady=(20, 5))
        
        score_label = tk.Label(score_frame, text="HIGH SCORE", 
                             font=("Press Start 2P", 12), fg="#00FFFF", bg="#000000")
        score_label.pack()
        
        self.high_score_label = tk.Label(score_frame, text=f"{self.high_score}", 
                                       font=("Press Start 2P", 16), fg="#00FFFF", bg="#000000")
        self.high_score_label.pack(pady=5)
        
        # Add a separator line
        separator = tk.Canvas(self.content_frame, width=300, height=2, bg="#000000",
                            highlightthickness=0)
        separator.pack(pady=10)
        separator.create_line(0, 1, 300, 1, fill="#00FFFF", width=2)
        
        # Title with neon glow effect
        title_frame = tk.Frame(self.content_frame, bg="#000000")
        title_frame.pack(pady=20)
        
        # Main title
        self.title_label = tk.Label(title_frame, text="2048 GAME", 
                                  font=("Press Start 2P", 28), fg="#FF00FF", bg="#000000")
        self.title_label.pack(pady=20)
        
        # Add another separator line
        separator2 = tk.Canvas(self.content_frame, width=300, height=2, bg="#000000",
                             highlightthickness=0)
        separator2.pack(pady=10)
        separator2.create_line(0, 1, 300, 1, fill="#FF00FF", width=2)
        
        # Main Menu Buttons
        button_frame = tk.Frame(self.content_frame, bg="#000000")
        button_frame.pack(pady=20)
        
        # Custom button style with neon effect
        self.create_neon_buttons(button_frame)
        
        # Initialize pygame for sound effects if not already initialized
        if not pygame.mixer.get_init():
            pygame.mixer.init()
    
    def create_neon_buttons(self, parent_frame):
        """Create buttons with neon glow effect"""
        buttons_info = [
            {"text": "New Game", "command": self.start_new_game, "color": "#00FFFF"},
            {"text": "Continue", "command": self.continue_game, "color": "#FF00FF"},
            {"text": "How to Play", "command": self.show_how_to_play, "color": "#FFFF00"},
            {"text": "Exit", "command": self.exit_game, "color": "#FF5555"}
        ]
        
        self.buttons = []
        
        for btn_info in buttons_info:
            # Create a button with cyberpunk styling
            button = tk.Button(
                parent_frame, 
                text=btn_info["text"],
                command=btn_info["command"],
                font=("Press Start 2P", 12),
                width=15, 
                height=2,
                bg="#111122",  # Dark background 
                fg=btn_info["color"],  # Neon text color
                activebackground="#222233",
                activeforeground=btn_info["color"],
                relief=tk.FLAT,
                borderwidth=2,
                highlightbackground=btn_info["color"],
                highlightcolor=btn_info["color"],
                highlightthickness=2
            )
            button.pack(pady=10)
            self.buttons.append(button)
    
    # Load pixel art background for the main menu
    def load_background(self):
        try:
            bg_path = os.path.join(os.path.dirname(__file__), "images", "menu_background.png")
            if os.path.exists(bg_path):
                img = Image.open(bg_path)
                img = img.resize((400, 600), Image.Resampling.LANCZOS)
                self.background_image = ImageTk.PhotoImage(img)
                
                # Create a label to display the background image
                self.bg_label = tk.Label(self.frame, image=self.background_image)
                self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
                
                # Configure the frame to have a transparent background
                self.frame.config(bg="#000000")
                print("Successfully loaded menu background image")
            else:
                print(f"Background image not found at {bg_path}")
        except Exception as e:
            print(f"Error loading background: {e}")
    
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
            # Use a more robust path that works in both script and executable modes
            app_data_dir = self.get_app_data_dir()
            high_score_path = os.path.join(app_data_dir, 'high_score.json')
            
            if os.path.exists(high_score_path):
                with open(high_score_path, 'r') as f:
                    data = json.load(f)
                    return data.get('high_score', 0)
            return 0
        except (FileNotFoundError, json.JSONDecodeError):
            return 0

    def get_app_data_dir(self):
        """Get a consistent directory for app data that works in both script and executable modes"""
        # For Windows, use AppData folder
        app_name = "2048Game"
        if hasattr(sys, 'frozen'):
            # Running as compiled executable
            base_dir = os.path.dirname(sys.executable)
        else:
            # Running as script
            base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Create a data directory in the same location as the executable/script
        data_dir = os.path.join(base_dir, 'data')
        return data_dir
    
    def start_new_game(self):
        """Start a new game"""
        # Clear the main menu
        for widget in self.master.winfo_children():
            widget.destroy()
        
        game = Game2048(self.master)
    
    def continue_game(self):
        """Load the last saved game state"""
        # Clear the main menu
        for widget in self.master.winfo_children():
            widget.destroy()
        
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
        - R: Restart game
        - M: Toggle sound
        - ESC: Show menu
        - Save Game: Save your current progress
        - Help: Show this help message
        - Quit: Exit the game
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
