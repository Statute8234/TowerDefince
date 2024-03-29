import pygame
import pygame_widgets
import pygame.sprite
from pygame import mixer
from pygame.surfarray import make_surface
from pygame_widgets.slider import Slider
from pygame_widgets.textbox import TextBox
# ---------------
import json
import random, time, sys
from perlin_noise import PerlinNoise
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
# color
def RANDOM_COLOR():
    return (random.randint(0,255),random.randint(0,255),random.randint(0,255))
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
BLACK = (0,0,0)
GRAY = (128,128,128)
DARK_GRAY = (169,169,169)
LIME = (0,255,0)
# json
class JsonHandler:
    def __init__(self, file_path):
        self.file_path = file_path

    def read_file(self):
        try:
            with open(self.file_path, 'r') as file:
                data = json.load(file)
            return data
        except FileNotFoundError:
            print(f"File '{self.file_path}' not found. Creating a new file.")
            return {}
        except json.decoder.JSONDecodeError:
            print(f"File '{self.file_path}' contains invalid JSON. Returning an empty dictionary.")
            return {}

    def write_file(self, data):
        with open(self.file_path, 'w') as file:
            json.dump(data, file, indent=4)

    def clear_file(self):
        with open(self.file_path, 'w') as file:
            file.truncate()

    def edit_file(self, key, new_data):
        data = self.read_file()
        if key in data:
            data[key] = new_data
            self.write_file(data)
            print(f"Data for '{key}' edited successfully.")
        else:
            print(f"Key '{key}' not found in the file.")
    
    def find_data(self, key):
        data = self.read_file()
        if key in data:
            return data[key]
        else:
            return None
        
    def append_to_file(self, key, value):
        data = self.read_file()
        # Check if the file is empty (data is an empty dictionary)
        if not data:
            data = {}  # If empty, initialize with an empty dictionary
        # Append new information to the existing data
        if key in data:
            data[key].append(value)
        else:
            data[key] = [value]
        # Write the updated data to the file
        self.write_file(data)
# ground Segment
class Segment:
    def __init__(self, x, y, width, height, active_color, inactive_color):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.active_color = active_color
        self.inactive_color = inactive_color
        self.color = self.inactive_color
        self.clicked = False

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
    
    def handle_event(self, event):
        mouse_pos = pygame.mouse.get_pos()
        if self.x < mouse_pos[0] < self.x + self.width and self.y < mouse_pos[1] < self.y + self.height:
            self.color = self.active_color
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.clicked = True
                    self.color = self.active_color
        else:
            self.color = self.inactive_color

    def reset(self):
        self.clicked = False
        self.color = self.inactive_color
# ground
class Ground:
    def __init__(self, screen_width, screen_height, cell_size):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.cell_size = cell_size
        self.width = screen_width // cell_size
        self.height = screen_height // cell_size
        self.freq = random.uniform(5, 30)
        self.amp = random.uniform(1, 15)
        self.octaves = random.randint(1, 6)
        self.seed = random.randint(0, sys.maxsize)
        self.water_threshold = random.triangular(0.0, 0.2, 0.5)
        self.pick = random.randint(0,1)
        self.biome_type_list = ['grassland','mountain','desert','snow','forest','swamp']
        self.biome_type = random.choice(self.biome_type_list)
        self.returnList = []
        self.segmentList = []
        self.ground_data = self.generate_ground()
        self.build()

    def get_biome_color(self, biome_type, brightness):
        if biome_type == 'water':
            color_value = int(brightness * 100) + random.randint(-10, 10)
            return (0, 0, max(0, min(255, color_value)))
        elif biome_type == 'grassland':
            color_value = int(brightness * 100) + random.randint(-10, 10)
            return (0, max(0, min(255, color_value)), 0)
        elif biome_type == 'mountain':
            color_value = int(brightness * 100) + random.randint(-10, 10)
            return (max(0, min(255, color_value)), max(0, min(255, color_value) - 50), max(0, min(255, color_value) - 100))
        elif biome_type == 'desert':
            base_color = (max(200, min(255, brightness * 255)), max(150, min(255, brightness * 255)), 0)
            color_variation = random.randint(-10, 10)
            return tuple(max(0, min(255, c + color_variation)) for c in base_color)
        elif biome_type == 'snow':
            base_color = (255, 255, 255)
            color_variation = random.randint(-10, 10)
            return tuple(max(0, min(255, c + color_variation)) for c in base_color)
        elif biome_type == 'forest':
            base_color = (0, max(50, min(150, brightness * 255)), 0)
            color_variation = random.randint(-10, 10)
            return tuple(max(0, min(255, c + color_variation)) for c in base_color)
        elif biome_type == 'swamp':
            base_color = (max(0, min(100, brightness * 255)), max(100, min(200, brightness * 255)), 0)
            color_variation = random.randint(-10, 10)
            return tuple(max(0, min(255, c + color_variation)) for c in base_color)
        
    def generate_ground(self):
        self.returnList = []
        noise = PerlinNoise(octaves=self.octaves, seed=self.seed)

        for i in range(self.width):
            for ii in range(self.height):
                cell_x = i / self.width
                cell_y = ii / self.height
                cell_height = noise([cell_x / self.freq, cell_y / self.freq]) * self.amp
                brightness = (cell_height + self.amp) / (2 * self.amp)
                brightness = max(0, min(1, brightness))
                # Adjust color based on height and add some randomness
                if self.pick == 1:
                    if cell_height < self.water_threshold:
                        biome_type = "water"
                    else:
                        biome_type = self.biome_type
                    color = self.get_biome_color(biome_type, brightness)
                    data_item = [(cell_x, cell_y), cell_height, color]
                    self.returnList.append(data_item)
                else:
                    color_value = int(brightness * 255) + random.randint(-10, 10)
                    color_value = max(0, min(255, color_value))
                    if cell_height < self.water_threshold:
                        color = (0, 0, color_value)
                    else:
                        color = (color_value, color_value - 50, color_value - 100)
                    data_item = [(cell_x, cell_y), cell_height, color]
                    self.returnList.append(data_item)
        return self.returnList

    def regenerate_map(self, biome_type = None):
        self.segmentList = []
        if biome_type == None:
            self.pick = random.randint(0,1)
            self.biome_type = random.choice(self.biome_type_list)
        else:
            self.pick = 1
            self.biome_type = biome_type
        self.ground_data = self.generate_ground()
        self.build()

    def to_json(self):
        json_data = {
            "screen_width": self.screen_width,
            "screen_height": self.screen_height,
            "cell_size": self.cell_size,
            "freq": self.freq,
            "amp": self.amp,
            "octaves": self.octaves,
            "seed": self.seed,
            "water_threshold": self.water_threshold,
            "pick": self.pick,
            "biome_type_list": self.biome_type_list,
            "biome_type": self.biome_type,
            "ground_data": self.ground_data
        }
        return json_data

    def from_json(self, json_data):
        self.screen_width = json_data["screen_width"]
        self.screen_height = json_data["screen_height"]
        self.cell_size = json_data["cell_size"]
        self.freq = json_data["freq"]
        self.amp = json_data["amp"]
        self.octaves = json_data["octaves"]
        self.seed = json_data["seed"]
        self.water_threshold = json_data["water_threshold"]
        self.pick = json_data["pick"]
        self.biome_type_list = json_data["biome_type_list"]
        self.biome_type = json_data["biome_type"]
        self.ground_data = json_data["ground_data"]
        self.build()

    def load_map(self, data):
        self.segmentList = []
        self.ground_data = data
        self.build()

    def build(self):
        for item in self.ground_data:
            cell_x, cell_y = item[0]
            cell_height = item[1]
            color = item[2]
            segment_width = self.screen_width // self.width
            segment_height = self.screen_height // self.height

            self.segment = Segment(cell_x * self.screen_width, cell_y * self.screen_height, segment_width, segment_height, LIME, color)
            self.segmentList.append(self.segment)

    def draw(self,screen):
        for item in self.segmentList:
            item.draw(screen)

    def handle_event(self, event):
        global showFull_map
        for item in self.segmentList:
            item.handle_event(event)
            if item.clicked:
                showFull_map = False
                item.reset()
