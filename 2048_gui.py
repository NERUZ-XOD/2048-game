import tkinter as tk
import numpy as np
import random

class Game2048:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("2048 Game")
        self.window.geometry("400x500")
        self.window.resizable(False, False)
        self.grid = np.zeros((4, 4), dtype=int)
        
        self.colors = {
            0: "#cdc1b4", 2: "#eee4da", 4: "#ede0c8", 8: "#f2b179",
            16: "#f59563", 32: "#f67c5f", 64: "#f65e3b", 128: "#edcf72",
            256: "#edcc61", 512: "#edc850", 1024: "#edc53f", 2048: "#edc22e"
        }
        
        self.init_ui()
        self.spawn_tile()
        self.spawn_tile()
        self.update_ui()

        self.window.bind("<Key>", self.handle_keypress)
        self.window.mainloop()
    
    def init_ui(self):
        self.frame = tk.Frame(self.window, bg="#bbada0")
        self.frame.pack(pady=20)
        self.tiles = [[tk.Label(self.frame, text="", font=("Arial", 20, "bold"), width=4, height=2, bg="#cdc1b4") 
                       for _ in range(4)] for _ in range(4)]
        
        for i in range(4):
            for j in range(4):
                self.tiles[i][j].grid(row=i, column=j, padx=5, pady=5)
    
    def update_ui(self):
        for i in range(4):
            for j in range(4):
                value = self.grid[i, j]
                self.tiles[i][j].config(text=str(value) if value else "", bg=self.colors.get(value, "#3c3a32"))
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
