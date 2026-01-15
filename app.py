import os
import re
import urllib.request
import json
import math
import random
from PIL import Image, ImageDraw
import streamlit as st
import requests
import io

# --- Groq API Key (your key pasted here) ---
GROQ_API_KEY = "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"

# --- Groq Endpoints ---
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_IMAGE_URL = "https://api.groq.com/openai/v1/images/generations"

# --- KNOWLEDGE ENGINE ---
class KnowledgeEngine:
    def __init__(self):
        self.cache = {}
    
    def search(self, query):
        raw_query = query.lower()
        if raw_query in self.cache:
            return self.cache[raw_query]
        
        try:
            result = self._search_wikipedia(query)
            self.cache[raw_query] = result
            return result
        except Exception as e:
            return f"Knowledge retrieval error: {e}"
    
    def _search_wikipedia(self, query):
        subject = query.lower()
        for word in ["what is the", "what is", "who is", "tell me about", "explain"]:
            subject = subject.replace(word, "")
        subject = subject.replace("?", "").strip()
        
        search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={subject.replace(' ', '%20')}&format=json"
        req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req, timeout=5) as r:
            s_data = json.loads(r.read().decode())
            results = s_data.get('query', {}).get('search', [])
            if not results:
                return "I couldn't find information about that."
            best_title = results[0]['title']
        
        content_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext&titles={best_title.replace(' ', '_')}&format=json&redirects=1"
        req2 = urllib.request.Request(content_url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req2, timeout=5) as r2:
            data = json.loads(r2.read().decode())
            page = list(data['query']['pages'].values())[0]
            full_text = page.get('extract', "")
            sentences = re.split(r'(?<=[.!?]) +', full_text)
            return " ".join(sentences[:4])

    # New: Step-by-step reasoning for queries
    def reason_and_respond(self, query):
        # Simple breakdown: Split query into key terms, search each, combine
        terms = re.split(r'\s+(and|or|about|with|in)\s+', query.lower())
        reasoning = "Let's reason step by step:\n"
        combined = ""
        for i, term in enumerate(terms[:3]):  # Limit to 3 for speed
            if term.strip():
                info = self.search(term.strip())
                reasoning += f"Step {i+1}: On '{term.strip()}': {info[:200]}...\n"
                combined += info + " "
        final = f"{reasoning}\nOverall: {combined[:500]}..."  # Truncate for brevity
        return final

# --- PROMPT PARSER WITH SPATIAL UNDERSTANDING ---
class PromptParser:
    def __init__(self):
        self.objects = {
            'car': ['car', 'vehicle', 'automobile'],
            'house': ['house', 'home', 'building'],
            'tree': ['tree', 'trees', 'forest'],
            'person': ['person', 'human', 'man', 'woman'],
            'sun': ['sun', 'sunshine'],
            'moon': ['moon'],
            'mountain': ['mountain', 'mountains'],
            'cloud': ['cloud', 'clouds'],
            'bird': ['bird', 'birds'],
            'flower': ['flower', 'flowers'],
            'road': ['road', 'street'],
            'water': ['water', 'lake', 'river'],
            'boat': ['boat', 'ship'],
            'city': ['city', 'skyline'],
            'dog': ['dog', 'puppy'],
            'cat': ['cat', 'kitten'],
            'star': ['star', 'stars'],
            'grass': ['grass', 'field'],
            'fence': ['fence'],
            'airplane': ['airplane', 'plane']
        }
        
        self.colors = {
            'red': ['red'], 'blue': ['blue'], 'green': ['green'],
            'yellow': ['yellow'], 'orange': ['orange'], 'purple': ['purple'],
            'black': ['black'], 'white': ['white'], 'brown': ['brown']
        }
        
        self.times = {
            'day': ['day', 'daytime'], 'night': ['night'], 
            'sunset': ['sunset'], 'sunrise': ['sunrise']
        }
        
        self.weather = {
            'sunny': ['sunny'], 'cloudy': ['cloudy'],
            'rainy': ['rain', 'rainy'], 'snowy': ['snow', 'snowy']
        }
    
    def parse(self, prompt):
        prompt_lower = prompt.lower()
        
        scene = {
            'objects': [],
            'colors': [],
            'time': 'day',
            'weather': 'sunny',
            'relationships': []
        }
        
        for obj, keywords in self.objects.items():
            if any(kw in prompt_lower for kw in keywords):
                scene['objects'].append(obj)
        
        for color, keywords in self.colors.items():
            if any(kw in prompt_lower for kw in keywords):
                scene['colors'].append(color)
        
        for time, keywords in self.times.items():
            if any(kw in prompt_lower for kw in keywords):
                scene['time'] = time
                break
        
        for weather, keywords in self.weather.items():
            if any(kw in prompt_lower for kw in keywords):
                scene['weather'] = weather
                break
        
        # Parse spatial relationships
        if 'car' in scene['objects'] and 'road' in scene['objects']:
            if 'on' in prompt_lower:
                scene['relationships'].append(('car', 'on', 'road'))
        
        if 'dog' in scene['objects'] and 'house' in scene['objects']:
            if 'in' in prompt_lower:
                scene['relationships'].append(('dog', 'in', 'house'))
        
        if 'cat' in scene['objects'] and 'house' in scene['objects']:
            if 'in' in prompt_lower:
                scene['relationships'].append(('cat', 'in', 'house'))
        
        if not scene['objects']:
            scene['objects'] = ['tree', 'house']
        
        return scene

# --- RENDERER WITH ADVANCED TEXTURES (Ported to Pillow) ---
class AdvancedRenderer:
    def __init__(self, width=500, height=500, resolution='1080p'):
        self.width = width
        self.height = height
        self.set_resolution(resolution)
    
    def set_resolution(self, res):
        res_map = {'480p': 1, '720p': 2, '1080p': 3, '4k': 5, '8k': 8}
        self.detail = res_map.get(res, 3)
        self.pixel_size = max(1, 3 // self.detail)
    
    def perlin_noise(self, x, y, scale=50):
        return (math.sin(x/scale) + math.cos(y/scale) + math.sin((x+y)/scale)) / 3
    
    def wood_texture(self, x, y, base_color):
        noise = self.perlin_noise(x, y, 20) * 0.3
        grain = math.sin(x / 3) * 0.15
        variation = noise + grain
        
        r = int(max(0, min(255, base_color[0] * (1 + variation))))
        g = int(max(0, min(255, base_color[1] * (1 + variation))))
        b = int(max(0, min(255, base_color[2] * (1 + variation))))
        return (r, g, b)
    
    def brick_texture(self, x, y, row):
        brick_offset = 20 if row % 2 == 0 else 0
        brick_x = (x + brick_offset) % 40
        brick_y = y % 15
        
        if brick_x < 2 or brick_y < 2:
            return (139, 134, 128)
        
        noise = self.perlin_noise(x + brick_offset, y, 10) * 0.2
        base = 160 + int(noise * 40)
        return (base, int(base*0.4), int(base*0.2))
    
    def grass_blade(self, draw, cx, cy, height, sway):
        points = []
        segments = 5
        
        for i in range(segments + 1):
            t = i / segments
            x = cx + math.sin(t * math.pi + sway) * (height * 0.1)
            y = cy - t * height
            points.extend([x, y])
        
        colors = [(45, 80, 22), (58, 107, 31), (71, 134, 41), (92, 161, 53)]
        for i in range(len(colors)):
            if i < segments:
                seg_start = i * 2
                draw.line((points[seg_start], points[seg_start + 1], points[seg_start + 2], points[seg_start + 3]), 
                          fill=colors[i], width=2)
    
    def render_scene(self, scene_data):
        img = Image.new('RGB', (self.width, self.height), 'black')
        draw = ImageDraw.Draw(img)
        
        self.draw_sky(draw, scene_data['time'], scene_data['weather'])
        self.draw_ground(draw, scene_data['time'])
        
        objects = scene_data['objects']
        relationships = scene_data.get('relationships', [])
        
        if 'mountain' in objects: self.draw_mountains(draw)
        if 'water' in objects: self.draw_water(draw)
        if 'city' in objects: self.draw_city(draw)
        if 'road' in objects: self.draw_road(draw)
        if 'grass' in objects: self.draw_grass_field(draw)
        if 'tree' in objects: self.draw_trees(draw, 3, True)
        
        house_drawn = False
        if 'house' in objects:
            self.draw_house(draw, scene_data.get('colors', []))
            house_drawn = True
        
        car_on_road = any(r == ('car', 'on', 'road') for r in relationships)
        if 'car' in objects:
            self.draw_car(draw, scene_data.get('colors', []), car_on_road)
        
        if 'boat' in objects: self.draw_boat(draw)
        
        dog_in_house = house_drawn and any(r == ('dog', 'in', 'house') for r in relationships)
        cat_in_house = house_drawn and any(r == ('cat', 'in', 'house') for r in relationships)
        
        if 'dog' in objects: self.draw_dog(draw, dog_in_house)
        if 'cat' in objects: self.draw_cat(draw, cat_in_house)
        if 'person' in objects: self.draw_person(draw)
        if 'airplane' in objects: self.draw_airplane(draw)
        if 'tree' in objects: self.draw_trees(draw, 2, False)
        if 'flower' in objects: self.draw_flowers(draw)
        if 'fence' in objects: self.draw_fence(draw)
        if 'sun' in objects or scene_data['time'] in ['day', 'sunset']: self.draw_sun(draw, scene_data['time'])
        if 'moon' in objects or scene_data['time'] == 'night': self.draw_moon(draw)
        if 'cloud' in objects or scene_data['weather'] == 'cloudy': self.draw_clouds(draw)
        if 'star' in objects or scene_data['time'] == 'night': self.draw_stars(draw)
        if 'bird' in objects: self.draw_birds(draw)
        if scene_data['weather'] == 'rainy': self.draw_rain(draw)
        if scene_data['weather'] == 'snowy': self.draw_snow(draw)
        
        return img
    
    def draw_sky(self, draw, time, weather):
        if time == 'night':
            colors = [(0, 4, 40), (0, 30, 80), (20, 50, 120)]
        elif time == 'sunset':
            colors = [(255, 107, 107), (255, 165, 0), (255, 215, 0), (135, 206, 250)]
        elif time == 'sunrise':
            colors = [(255, 182, 193), (255, 160, 122), (135, 206, 235)]
        else:
            colors = [(135, 206, 235), (100, 149, 237), (70, 130, 220)]
        
        steps = 100
        for i in range(steps):
            progress = i / steps
            section = int(progress * (len(colors) - 1))
            local_progress = (progress * (len(colors) - 1)) - section
            
            if section >= len(colors) - 1:
                color = colors[-1]
            else:
                c1, c2 = colors[section], colors[section + 1]
                r = int(c1[0] + (c2[0] - c1[0]) * local_progress)
                g = int(c1[1] + (c2[1] - c1[1]) * local_progress)
                b = int(c1[2] + (c2[2] - c1[2]) * local_progress)
                color = (r, g, b)
            
            y = int(i * self.height // 2 / steps)
            draw.rectangle((0, y, self.width, y + 5), fill=color)
    
    def draw_ground(self, draw, time):
        if time == 'night':
            colors = [(26, 77, 46), (15, 50, 30)]
        else:
            colors = [(74, 124, 89), (60, 100, 70), (50, 85, 60)]
        
        ground_y = self.height // 2
        steps = 50
        for i in range(steps):
            progress = i / steps
            section = int(progress * (len(colors) - 1))
            
            if section >= len(colors) - 1:
                color = colors[-1]
            else:
                c1, c2 = colors[section], colors[section + 1]
                local = (progress * (len(colors) - 1)) - section
                r = int(c1[0] + (c2[0] - c1[0]) * local)
                g = int(c1[1] + (c2[1] - c1[1]) * local)
                b = int(c1[2] + (c2[2] - c1[2]) * local)
                color = (r, g, b)
            
            y = ground_y + int(i * (self.height - ground_y) / steps)
            draw.rectangle((0, y, self.width, y + 10), fill=color)
    
    def darken(self, color, factor=0.5):
        r, g, b = color
        return (int(r*factor), int(g*factor), int(b*factor))
    
    def draw_house(self, draw, colors):
        x, y = 150, 200
        
        if 'brown' in colors:
            wall = (139, 90, 43)
        elif 'red' in colors:
            wall = (178, 34, 34)
        else:
            wall = (210, 180, 140)
        
        roof = (101, 67, 33)
        
        # 3D Shadow
        for offset in range(12, 0, -1):
            alpha = 1 - (offset / 14)
            shadow = self.darken(wall, alpha * 0.25)
            draw.polygon((x+offset, y+78, x+108+offset, y+78, x+108+offset, y+158, x+offset, y+158), fill=shadow)
        
        # WOOD TEXTURED WALLS
        for py in range(80):
            for px in range(100):
                actual_x = x + px
                actual_y = y + 70 + py
                
                wood_color = self.wood_texture(actual_x, actual_y, wall)
                
                brightness = 1 - (py / 160)
                
                r, g, b = wood_color
                r = int(r * brightness)
                g = int(g * brightness)
                b = int(b * brightness)
                final_color = (r, g, b)
                
                if px % 2 == 0 and py % 2 == 0:
                    draw.rectangle((actual_x, actual_y, actual_x+2, actual_y+2), fill=final_color)
        
        # Wall outline
        draw.rectangle((x, y+70, x+100, y+150), outline=(0,0,0), width=3)
        
        # BRICK TEXTURED ROOF
        # Back roof
        for ry in range(y+20, y+70, 2):
            row = (ry - (y+20)) // 2
            for rx in range(x+50, x+110, 2):
                brick_col = self.brick_texture(rx, ry, row)
                draw.rectangle((rx, ry, rx+2, ry+2), fill=brick_col)
        
        # Roof edges
        draw.polygon((x+50, y+20, x+110, y+70, x+100, y+70, x+50, y+30), outline=(0,0,0), width=2)
        
        # Front roof
        for ry in range(y+30, y+70, 4):
            for rx in range(x-10, x+100, 8):
                shingle_darkness = 1 - ((ry - (y+30)) / 40 * 0.3)
                shingle_r = int(roof[0] * shingle_darkness)
                shingle_g = int(roof[1] * shingle_darkness)
                shingle_b = int(roof[2] * shingle_darkness)
                
                noise = self.perlin_noise(rx, ry, 15) * 0.2
                shingle_r = int(shingle_r * (1 + noise))
                shingle_g = int(shingle_g * (1 + noise))
                shingle_b = int(shingle_b * (1 + noise))
                
                shingle_color = (shingle_r, shingle_g, shingle_b)
                draw.rectangle((rx, ry, rx+7, ry+3), fill=shingle_color, outline=(101,67,33))
        
        draw.polygon((x+50, y+30, x-10, y+70, x+100, y+70), outline=(0,0,0), width=3)
        
        # DETAILED WOODEN DOOR
        door_wood = (101, 67, 33)
        for dy in range(40):
            for dx in range(20):
                door_x = x + 40 + dx
                door_y = y + 110 + dy
                
                plank_noise = math.sin(dx / 4) * 0.15
                wood_col = self.wood_texture(door_x, door_y, door_wood)
                
                r, g, b = wood_col
                r = int(r * (1 + plank_noise))
                g = int(g * (1 + plank_noise))
                b = int(b * (1 + plank_noise))
                
                door_color = (r, g, b)
                draw.point((door_x, door_y), fill=door_color)
        
        # Door frame
        draw.rectangle((x+40, y+110, x+60, y+150), outline=(0,0,0), width=3)
        
        # Door panels
        draw.rectangle((x+42, y+112, x+58, y+135), outline=(101,67,33), width=2)
        draw.rectangle((x+42, y+137, x+58, y+148), outline=(101,67,33), width=2)
        
        # Door knob
        for r in range(4, 0, -1):
            shine = 1 + (4 - r) * 0.3
            knob_color = (min(255, int(218*shine)), min(255, int(165*shine)), 0)
            draw.ellipse((x+54-r, y+129-r, x+54+r, y+129+r), fill=knob_color)
        draw.ellipse((x+54, y+129, x+59, y+134), outline=(0,0,0), width=1)
        draw.ellipse((x+55, y+130, x+56, y+131), fill=(255,255,255))
        
        # REALISTIC GLASS WINDOWS
        for wx_base in [x+15, x+65]:
            # Window frame
            for fy in range(20):
                for fx in range(20):
                    frame_x = wx_base + fx
                    frame_y = y + 90 + fy
                    
                    if fx < 2 or fx > 18 or fy < 2 or fy > 18:
                        frame_color = self.wood_texture(frame_x, frame_y, (101, 67, 33))
                        draw.point((frame_x, frame_y), fill=frame_color)
            
            # Glass
            for gy in range(16):
                for gx in range(16):
                    glass_x = wx_base + 2 + gx
                    glass_y = y + 92 + gy
                    
                    reflection = 1 - (gy / 20)
                    glass_r = int(135 * (0.7 + reflection * 0.3))
                    glass_g = int(206 * (0.7 + reflection * 0.3))
                    glass_b = int(235 * (0.7 + reflection * 0.3))
                    
                    noise = self.perlin_noise(glass_x, glass_y, 30) * 0.1
                    glass_r = int(glass_r * (1 + noise))
                    glass_g = int(glass_g * (1 + noise))
                    glass_b = int(glass_b * (1 + noise))
                    
                    glass_color = (glass_r, glass_g, glass_b)
                    draw.point((glass_x, glass_y), fill=glass_color)
            
            # Window cross bars
            draw.line((wx_base+10, y+90, wx_base+10, y+110), fill=(47,79,79), width=2)
            draw.line((wx_base, y+100, wx_base+20, y+100), fill=(47,79,79), width=2)
            
            # Reflection spot
            draw.rectangle((wx_base+3, y+93, wx_base+8, y+98), fill=(255,255,255))
            draw.rectangle((wx_base+4, y+94, wx_base+6, y+96), fill=(240,255,255))
            
            # Outline
            draw.rectangle((wx_base, y+90, wx_base+20, y+110), outline=(0,0,0), width=2)
        
        # BRICK CHIMNEY
        for cy in range(y+40, y+70, 3):
            row = (cy - (y+40)) // 3
            for cx in range(x+70, x+85, 2):
                brick_col = self.brick_texture(cx, cy, row)
                draw.rectangle((cx, cy, cx+2, cy+3), fill=brick_col, outline=(101,67,33))
        
        draw.rectangle((x+70, y+40, x+85, y+70), outline=(0,0,0), width=2)
        
        # Chimney side
        draw.polygon((x+85, y+40, x+90, y+43, x+90, y+70, x+85, y+70), fill=(101,67,33), outline=(0,0,0), width=1)
    
    def draw_car(self, draw, colors, on_road=False):
        x, y = (220, 310) if on_road else (320, 230)
        
        if 'red' in colors:
            car_color = (220, 20, 60)
        elif 'blue' in colors:
            car_color = (30, 60, 200)
        elif 'yellow' in colors:
            car_color = (255, 215, 0)
        else:
            car_color = (70, 70, 90)
        
        # Shadow
        for offset in range(10, 0, -2):
            alpha = 1 - (offset / 12)
            shadow = self.darken(car_color, alpha * 0.2)
            draw.ellipse((x+offset, y+58+offset, x+108+offset, y+68+offset), fill=shadow)
        
        # Body gradient
        for i in range(30):
            shine = 1 + (abs(15 - i) / 30)
            r = min(255, int(car_color[0] * shine))
            g = min(255, int(car_color[1] * shine))
            b = min(255, int(car_color[2] * shine))
            body_color = (r, g, b)
            draw.rectangle((x, y+30+i, x+100, y+31+i), fill=body_color)
        
        # Body outline
        draw.rectangle((x, y+30, x+100, y+60), outline=(0,0,0), width=2)
        
        # Cabin
        cabin_dark = self.darken(car_color, 0.3)
        draw.polygon((x+20, y+10, x+70, y+10, x+80, y+30, x+10, y+30), fill=cabin_dark, outline=(0,0,0), width=2)
        
        # Windows
        # Front window
        for i in range(16):
            glass_brightness = 0.6 + (i / 40)
            glass = (int(135*glass_brightness), int(206*glass_brightness), int(235*glass_brightness))
            draw.line((x+22+i, y+12, x+18+i, y+28), fill=glass, width=2)
        draw.polygon((x+22, y+12, x+45, y+12, x+48, y+28, x+18, y+28), outline=(0,0,0), width=1)
        
        # Side window
        for i in range(20):
            glass_brightness = 0.5 + (i / 50)
            glass = (int(100*glass_brightness), int(149*glass_brightness), int(237*glass_brightness))
            draw.line((x+50+i, y+12, x+50+i, y+28), fill=glass, width=2)
        draw.polygon((x+48, y+12, x+68, y+12, x+78, y+28, x+50, y+28), outline=(0,0,0), width=1)
        
        # Window reflection
        draw.polygon((x+23, y+13, x+32, y+13, x+30, y+20, x+20, y+20), fill=(255,255,255))
        draw.polygon((x+24, y+14, x+28, y+14, x+27, y+18, x+22, y+18), fill=(240,255,255))
        
        # Wheels
        for wx in [x+10, x+70]:
            # Tire
            for r in range(20, 10, -1):
                darkness = 1 - ((20 - r) / 20)
                tire_color = (int(47*darkness), int(79*darkness), int(79*darkness))
                draw.ellipse((wx+10-r, y+50+10-r, wx+10+r, y+50+10+r), fill=tire_color)
            
            draw.ellipse((wx, y+50, wx+20, y+70), outline=(0,0,0), width=2)
            
            # Chrome rim
            for r in range(8, 3, -1):
                chrome_brightness = 1.5 - (r / 16)
                chrome = int(192 * chrome_brightness)
                chrome_color = (chrome, chrome, chrome)
                draw.ellipse((wx+10-r, y+60-r, wx+10+r, y+60+r), fill=chrome_color)
            
            draw.ellipse((wx+5, y+55, wx+15, y+65), outline=(0,0,0), width=1)
            
            # Spokes
            for angle in range(0, 360, 72):
                rad = math.radians(angle)
                x1, y1 = wx+10, y+60
                x2 = x1 + int(5 * math.cos(rad))
                y2 = y1 + int(5 * math.sin(rad))
                draw.line((x1, y1, x2, y2), fill=(169,169,169), width=1)
        
        # Headlights
        for glow in range(5, 0, -1):
            alpha = 1 - (glow / 6)
            glow_color = (255, 255, int(alpha * 255))
            draw.ellipse((x+92-glow, y+38-glow, x+98+glow, y+44+glow), fill=glow_color)
        draw.ellipse((x+92, y+38, x+98, y+44), fill=(255,255,0), outline=(255,215,0), width=1)
        draw.ellipse((x+93, y+39, x+95, y+41), fill=(255,255,255))
        
        # Door line
        draw.line((x+50, y+30, x+50, y+60), fill=(0,0,0), width=2)
        draw.line((x+51, y+31, x+51, y+59), fill=(85,85,85), width=1)
        
        # Door handle
        draw.rectangle((x+55, y+45, x+65, y+48), fill=(192,192,192), outline=(128,128,128), width=1)
        draw.ellipse((x+56, y+46, x+57, y+47), fill=(255,255,255))
    
    def draw_trees(self, draw, count, bg):
        positions = [(50, 180), (400, 180), (180, 180)] if bg else [(30, 220), (450, 220)]
        scale = 0.7 if bg else 1.0
        
        for tx, ty in positions[:count]:
            trunk_w = int(12 * scale)
            trunk_h = int(50 * scale)
            
            # Shadow
            for offset in range(int(8*scale), 0, -1):
                alpha = 1 - (offset / (10*scale))
                shadow = int(26 * alpha * 0.3)
                shadow_color = (shadow, shadow, shadow)
                draw.rectangle((tx+offset-trunk_w//2, ty+offset, tx+offset+trunk_w//2, ty+offset+trunk_h), fill=shadow_color)
            
            # Trunk texture
            for i in range(trunk_h):
                bark_var = random.randint(-15, 15)
                bark_brightness = 1 - (i / trunk_h * 0.3)
                bark_r = max(0, min(255, int((101 + bark_var) * bark_brightness)))
                bark_g = max(0, min(255, int((67 + bark_var) * bark_brightness)))
                bark_b = max(0, min(255, int((33 + bark_var) * bark_brightness)))
                bark_color = (bark_r, bark_g, bark_b)
                draw.rectangle((tx-trunk_w//2, ty+i, tx+trunk_w//2, ty+i+1), fill=bark_color)
            
            draw.rectangle((tx-trunk_w//2, ty, tx+trunk_w//2, ty+trunk_h), outline=(0,0,0), width=1)
            
            # Foliage
            foliage_layers = [
                (34, 139, 34, 0, int(30*scale)),
                (46, 139, 87, -int(15*scale), int(25*scale)),
                (50, 205, 50, -int(25*scale), int(20*scale))
            ]
            
            for r_val, g_val, b_val, offset, radius in foliage_layers:
                for cluster in range(int(8 * scale)):
                    angle = cluster * 45
                    rad = math.radians(angle)
                    cx = tx + int(radius * 0.3 * math.cos(rad))
                    cy = ty + offset + int(radius * 0.3 * math.sin(rad))
                    
                    for i in range(radius, 0, -2):
                        brightness = 1 - ((radius - i) / radius * 0.4)
                        leaf_r = int(r_val * brightness)
                        leaf_g = int(g_val * brightness)
                        leaf_b = int(b_val * brightness)
                        leaf_color = (leaf_r, leaf_g, leaf_b)
                        draw.ellipse((cx-i, cy-i, cx+i, cy+i), fill=leaf_color)
                
                for i in range(radius, 0, -1):
                    brightness = 1 - ((radius - i) / radius * 0.3)
                    leaf_r = int(r_val * brightness)
                    leaf_g = int(g_val * brightness)
                    leaf_b = int(b_val * brightness)
                    leaf_color = (leaf_r, leaf_g, leaf_b)
                    draw.ellipse((tx-i, ty+offset-i, tx+i, ty+offset+i), fill=leaf_color)
                
                draw.ellipse((tx-radius, ty+offset-radius, tx+radius, ty+offset+radius), outline=(26,93,26), width=1)
    
    def draw_mountains(self, draw):
        points = [(0, 250), (100, 150), (250, 120), (450, 140), (500, 250)]
        
        # Fill with texture
        for y in range(120, 250):
            for x in range(0, 500, 2):
                if self.point_in_mountain(x, y, points):
                    noise = self.perlin_noise(x, y, 15) * 0.3
                    height_factor = 1 - ((y - 120) / 130)
                    base_gray = 105 + int(height_factor * 50)
                    gray = int(base_gray * (1 + noise))
                    if random.random() < 0.1:
                        gray += random.randint(-20, 20)
                    rock_color = (gray, gray, gray)
                    draw.rectangle((x, y, x+2, y+2), fill=rock_color)
        
        draw.polygon(points, outline=(0,0,0), width=2)
        
        # Snow caps
        snow_peaks = [
            (100, 150, 120, 160, 80, 160),
            (250, 120, 270, 135, 230, 135),
            (450, 140, 465, 152, 435, 152)
        ]
        
        for peak in snow_peaks:
            for sy in range(int(peak[1]), int(peak[3])):
                for sx in range(int(peak[4]), int(peak[2])):
                    if self.point_in_triangle(sx, sy, peak[0], peak[1], peak[2], peak[3], peak[4], peak[5]):
                        snow_noise = self.perlin_noise(sx, sy, 8) * 0.2
                        snow_val = int(255 * (0.9 + snow_noise))
                        snow_color = (snow_val, snow_val, snow_val)
                        draw.point((sx, sy), fill=snow_color)
            
            draw.polygon(peak, outline=(208,208,208), width=1)
    
    def point_in_mountain(self, x, y, points):
        return 120 <= y <= 250 and 0 <= x <= 500
    
    def point_in_triangle(self, x, y, x1, y1, x2, y2, x3, y3):
        def sign(px, py, ax, ay, bx, by):
            return (px - bx) * (ay - by) - (ax - bx) * (py - by)
        
        d1 = sign(x, y, x1, y1, x2, y2)
        d2 = sign(x, y, x2, y2, x3, y3)
        d3 = sign(x, y, x3, y3, x1, y1)
        
        has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
        has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
        
        return not (has_neg and has_pos)
    
    def draw_water(self, draw):
        y_start = 250
        
        for i in range(0, self.height - y_start, 1):
            y = y_start + i
            depth = i / (self.height - y_start)
            
            base_r = int(65 * (1 - depth * 0.3))
            base_g = int(105 * (1 - depth * 0.3))
            base_b = int(225 * (1 - depth * 0.2))
            
            wave = math.sin(i / 10) * 10 + math.cos(i / 7) * 5
            noise = self.perlin_noise(0, y + wave, 30) * 0.2
            
            r = int(base_r * (1 + noise))
            g = int(base_g * (1 + noise))
            b = int(base_b * (1 + noise))
            
            color = (r, g, b)
            draw.rectangle((0, y, self.width, y + 1), fill=color)
        
        # Ripples
        for i in range(8):
            y = y_start + 30 + i * 30
            
            for x in range(0, self.width, 15):
                ripple_offset = math.sin(x / 20 + i) * 3
                ripple_y = y + ripple_offset
                
                draw.ellipse((x-3, ripple_y-1, x+3, ripple_y+1), fill=(176,224,230))
                draw.ellipse((x-2, ripple_y+2, x+2, ripple_y+3), fill=(70,130,180))
        
        # Foam
        for _ in range(50 * self.detail):
            fx = random.randint(0, self.width)
            fy = random.randint(y_start, y_start + 100)
            foam_size = random.randint(1, 3)
            
            draw.ellipse((fx, fy, fx+foam_size, fy+foam_size), fill=(240,255,255))
    
    def draw_sun(self, draw, time):
        x, y = (100, 100) if time == 'sunset' else (420, 80)
        color = (255, 69, 0) if time == 'sunset' else (255, 215, 0)
        
        # Glow
        for i in range(40, 0, -3):
            alpha = 1 - (i / 45)
            glow_r = int(color[0] * (0.5 + alpha * 0.5))
            glow_g = int(color[1] * (0.5 + alpha * 0.5))
            glow_b = int(max(0, color[2] - 50) * (0.5 + alpha * 0.5))
            glow_color = (glow_r, glow_g, glow_b)
            draw.ellipse((x-i, y-i, x+i, y+i), fill=glow_color)
        
        # Core
        for i in range(25, 0, -1):
            brightness = 1 + ((25 - i) / 50)
            core_r = min(255, int(color[0] * brightness))
            core_g = min(255, int(color[1] * brightness))
            core_b = min(255, int(color[2] * brightness))
            core_color = (core_r, core_g, core_b)
            draw.ellipse((x-i, y-i, x+i, y+i), fill=core_color)
        
        # Edge
        draw.ellipse((x-22, y-22, x+22, y+22), outline=(int(color[0]*0.8), int(color[1]*0.6), int(color[2]*0.3)), width=2)
        
        # Rays
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            x1 = x + int(28 * math.cos(rad))
            y1 = y + int(28 * math.sin(rad))
            x2 = x + int(45 * math.cos(rad))
            y2 = y + int(45 * math.sin(rad))
            
            ray_color = (color[0], int(color[1]*0.9), int(color[2]*0.7))
            draw.line((x1, y1, x2, y2), fill=ray_color, width=2)
    
    def draw_moon(self, draw):
        x, y = 420, 80
        
        # Glow
        for i in range(35, 0, -3):
            alpha = 1 - (i / 40)
            glow = int(240 * (0.3 + alpha * 0.7))
            glow_color = (glow, glow, int(glow*0.9))
            draw.ellipse((x-i, y-i, x+i, y+i), fill=glow_color)
        
        # Surface
        for i in range(28, 0, -1):
            brightness = 0.85 + ((28 - i) / 100)
            moon_color = (int(240*brightness), int(230*brightness), int(140*brightness))
            draw.ellipse((x-i, y-i, x+i, y+i), fill=moon_color)
        
        # Outline
        draw.ellipse((x-27, y-27, x+27, y+27), outline=(218,165,32), width=2)
        
        # Craters
        craters = [
            (x-10, y-8, x-2, y, (211,211,211), (169,169,169)),
            (x+5, y+3, x+12, y+10, (192,192,192), (160,160,160)),
            (x-5, y+8, x+2, y+15, (211,211,211), (176,176,176)),
            (x+10, y-15, x+16, y-9, (200,200,200), (168,168,168))
        ]
        
        for x1, y1, x2, y2, light, dark in craters:
            draw.ellipse((x1, y1, x2, y2), fill=dark)
            offset = 2
            draw.ellipse((x1-offset, y1-offset, x2-offset, y2-offset), fill=light)
    
    def draw_clouds(self, draw):
        positions = [(100, 80), (300, 60), (450, 90)]
        
        for cx, cy in positions:
            puffs = [
                (cx, cy, 40, 25),
                (cx+20, cy-5, 35, 20),
                (cx+35, cy, 30, 25)
            ]
            
            for px, py, width, height in puffs:
                for r in range(max(width, height), 0, -2):
                    brightness = 1 - (r / max(width, height)) * 0.15
                    cloud_val = int(255 * brightness)
                    noise = self.perlin_noise(px + r, py, 12) * 0.05
                    cloud_val = int(cloud_val * (1 - noise))
                    cloud_color = (cloud_val, cloud_val, cloud_val)
                    draw.ellipse((px-r//2, py-r//3, px+r//2, py+r//3), fill=cloud_color)
            
            draw.ellipse((cx, cy, cx+40, cy+25), outline=(224,224,224), width=1)
            draw.ellipse((cx+20, cy-5, cx+55, cy+15), outline=(224,224,224), width=1)
            draw.ellipse((cx+35, cy, cx+65, cy+25), outline=(224,224,224), width=1)
    
    def draw_stars(self, draw):
        for _ in range(40 * self.detail):
            x, y = random.randint(0, self.width), random.randint(0, 150)
            draw.ellipse((x, y, x+2, y+2), fill=(255,255,255))
    
    def draw_road(self, draw):
        road_points = [200, 250, 300, 250, 400, 500, 100, 500]
        
        # Asphalt
        for y in range(250, 500, 2):
            progress = (y - 250) / 250
            left_x = 200 - progress * 100
            right_x = 300 + progress * 100
            width = right_x - left_x
            
            for x_offset in range(0, int(width), 2):
                px = left_x + x_offset
                py = y
                
                base_gray = 105
                noise = self.perlin_noise(px, py, 8) * 30
                gray = int(max(60, min(140, base_gray + noise)))
                if random.random() < 0.05:
                    gray += random.randint(-20, 20)
                asphalt_color = (gray, gray, gray)
                draw.rectangle((px, py, px+2, py+2), fill=asphalt_color)
        
        draw.polygon(road_points, outline=(0,0,0), width=3)
        
        # Yellow lines
        for i in range(5):
            y1 = 270 + i * 45
            y2 = y1 + 25
            
            progress1 = (y1 - 270) / 230
            progress2 = (y2 - 270) / 230
            
            w1 = 4 + progress1 * 4
            w2 = 4 + progress2 * 4
            
            x1_left = 250 - w1
            x1_right = 250 + w1
            x2_left = 250 - w2
            x2_right = 250 + w2
            
            for ly in range(int(y2 - y1)):
                line_y = y1 + ly
                line_progress = ly / (y2 - y1)
                
                line_left = x1_left + (x2_left - x1_left) * line_progress
                line_right = x1_right + (x2_right - x1_right) * line_progress
                
                fade = 1 - random.random() * 0.3
                yellow_color = (int(255*fade), int(255*fade), 0)
                draw.rectangle((line_left, line_y, line_right, line_y+1), fill=yellow_color)
        
        # Cracks
        for _ in range(15):
            crack_x = random.randint(150, 350)
            crack_y = random.randint(270, 480)
            crack_length = random.randint(10, 40)
            
            cx, cy = crack_x, crack_y
            for _ in range(crack_length):
                next_x = cx + random.randint(-2, 2)
                next_y = cy + random.randint(1, 3)
                draw.line((cx, cy, next_x, next_y), fill=(26,26,26), width=1)
                cx, cy = next_x, next_y
    
    def draw_grass_field(self, draw):
        grass_count = 200 * self.detail
        
        for _ in range(grass_count):
            x = random.randint(0, self.width)
            y = random.randint(250, 400)
            
            height = random.randint(5, 12)
            sway = random.uniform(-0.3, 0.3)
            
            self.grass_blade(draw, x, y, height, sway)
        
        for _ in range(30 * self.detail):
            cx = random.randint(0, self.width)
            cy = random.randint(270, 390)
            
            for i in range(random.randint(3, 7)):
                offset_x = random.randint(-5, 5)
                offset_y = random.randint(-3, 3)
                height = random.randint(8, 15)
                sway = random.uniform(-0.2, 0.2)
                
                self.grass_blade(draw, cx + offset_x, cy + offset_y, height, sway)
    
    def draw_person(self, draw):
        x, y = 280, 220
        draw.ellipse((x-8, y, x+8, y+16), fill=(255,217,179), outline=(0,0,0), width=2)
        draw.line((x, y+16, x, y+35), fill=(0,0,0), width=3)
        draw.line((x, y+20, x-12, y+30), fill=(0,0,0), width=3)
        draw.line((x, y+20, x+12, y+30), fill=(0,0,0), width=3)
        draw.line((x, y+35, x-8, y+55), fill=(0,0,0), width=3)
        draw.line((x, y+35, x+8, y+55), fill=(0,0,0), width=3)
    
    def draw_dog(self, draw, in_house):
        x, y = (195, 275) if in_house else (350, 240)
        draw.ellipse((x, y+10, x+30, y+25), fill=(139,69,19), outline=(0,0,0), width=2)
        draw.ellipse((x+22, y, x+38, y+15), fill=(160,82,45), outline=(0,0,0), width=2)
        for leg_x in [x+5, x+12, x+18, x+25]:
            draw.rectangle((leg_x, y+23, leg_x+3, y+33), fill=(101,67,33), outline=(0,0,0))
    
    def draw_cat(self, draw, in_house):
        x, y = (195, 280) if in_house else (380, 245)
        draw.ellipse((x, y+5, x+25, y+18), fill=(255,165,0), outline=(0,0,0), width=2)
        draw.ellipse((x+18, y-2, x+32, y+10), fill=(255,165,0), outline=(0,0,0), width=2)
    
    def draw_boat(self, draw):
        x, y = 200, 270
        
        hull_base = (139, 69, 19)
        
        # Hull planks
        for hy in range(20):
            plank_row = hy // 4
            for hx in range(80):
                hull_x = x - 10 + hx
                hull_y = y + hy
                
                plank_noise = math.sin(plank_row * 2) * 0.1
                wood_col = self.wood_texture(hull_x, hull_y, hull_base)
                
                r, g, b = wood_col
                r = int(r * (1 + plank_noise))
                g = int(g * (1 + plank_noise))
                b = int(b * (1 + plank_noise))
                
                hull_color = (r, g, b)
                draw.point((hull_x, hull_y), fill=hull_color)
        
        draw.polygon((x, y, x+60, y, x+70, y+20, x-10, y+20), outline=(0,0,0), width=2)
        
        # Interior
        interior_wood = (210, 105, 30)
        for iy in range(13):
            for ix in range(60):
                int_x = x + 5 + ix
                int_y = y + 5 + iy
                
                int_color = self.wood_texture(int_x, int_y, interior_wood)
                draw.point((int_x, int_y), fill=int_color)
        
        draw.polygon((x+5, y+5, x+55, y+5, x+62, y+18, x-2, y+18), outline=(101,67,33), width=1)
        
        # Mast
        for my in range(45):
            mast_color = self.wood_texture(x+30, y+5-my, (101, 67, 33))
            draw.line((x+30, y+5-my, x+30, y+6-my), fill=mast_color, width=4)
        
        # Sail
        sail_points = [x+30, y-35, x+55, y-10, x+30, y+5]
        
        for sy in range(y-35, y+5):
            for sx in range(x+30, x+55):
                if self.point_in_sail(sx, sy, sail_points):
                    weave = (math.sin(sx * 0.5) + math.cos(sy * 0.5)) * 0.1
                    fabric_val = int(245 * (1 + weave))
                    billow = math.sin((sy - (y-35)) / 5) * 0.05
                    fabric_val = int(fabric_val * (1 + billow))
                    sail_color = (fabric_val, fabric_val, fabric_val)
                    draw.point((sx, sy), fill=sail_color)
        
        draw.polygon(sail_points, outline=(0,0,0), width=2)
        
        # Seams
        for seam_y in range(y-35, y+5, 10):
            seam_x1 = x + 30
            seam_x2 = x + 30 + int((seam_y - (y-35)) / 45 * 25)
            draw.line((seam_x1, seam_y, seam_x2, seam_y), fill=(208,208,208), width=1)
    
    def point_in_sail(self, x, y, points):
        x1, y1, x2, y2, x3, y3 = points
        
        def sign(px, py, ax, ay, bx, by):
            return (px - bx) * (ay - by) - (ax - bx) * (py - by)
        
        d1 = sign(x, y, x1, y1, x2, y2)
        d2 = sign(x, y, x2, y2, x3, y3)
        d3 = sign(x, y, x3, y3, x1, y1)
        
        has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
        has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
        
        return not (has_neg and has_pos)
    
    def draw_flowers(self, draw):
        positions = [(80, 280), (120, 290), (420, 285), (460, 295)]
        colors = [(255, 20, 147), (255, 105, 180), (255, 215, 0), (255, 69, 0)]
        
        for (fx, fy), (r, g, b) in zip(positions, colors):
            # Stem
            for sy in range(20):
                stem_noise = self.perlin_noise(fx, fy + sy, 5) * 0.2
                stem_green = int(34 * (1 + stem_noise))
                stem_color = (stem_green, int(139*(1+stem_noise*0.5)), int(34*(1+stem_noise)))
                draw.line((fx, fy+sy, fx, fy+sy+1), fill=stem_color, width=3)
            
            # Leaves
            for lx, ly in [(fx-5, fy+10), (fx+5, fy+15)]:
                for i in range(5):
                    leaf_color = (int(34+i*5), int(139+i*3), int(34+i*5))
                    draw.ellipse((lx-3+i//2, ly-2+i//3, lx+3-i//2, ly+2-i//3), fill=leaf_color, outline=(34,139,34))
            
            # Petals
            for angle in range(0, 360, 60):
                rad = math.radians(angle)
                px = fx + 6 * math.cos(rad)
                py = fy + 6 * math.sin(rad)
                
                for i in range(5, 0, -1):
                    brightness = 0.7 + (5 - i) * 0.06
                    petal_r = int(r * brightness)
                    petal_g = int(g * brightness)
                    petal_b = int(b * brightness)
                    petal_color = (petal_r, petal_g, petal_b)
                    draw.ellipse((px-i, py-i, px+i, py+i), fill=petal_color)
                
                draw.ellipse((px-4, py-4, px+4, py+4), outline=(int(r*0.8), int(g*0.8), int(b*0.8)), width=1)
            
            # Center
            for i in range(4, 0, -1):
                center_brightness = 1 + (4 - i) * 0.1
                center_val = int(min(255, 218 * center_brightness))
                center_color = (center_val, int(center_val*0.9), 0)
                draw.ellipse((fx-i, fy-i, fx+i, fy+i), fill=center_color)
            
            for _ in range(5):
                dot_x = fx + random.randint(-2, 2)
                dot_y = fy + random.randint(-2, 2)
                draw.ellipse((dot_x, dot_y, dot_x+1, dot_y+1), fill=(255,165,0))
    
    def draw_fence(self, draw):
        y = 260
        
        for fx in range(0, self.width, 40):
            # Post
            for py in range(50):
                for px in range(8):
                    post_x = fx + px
                    post_y = y + py
                    
                    wood_color = self.wood_texture(post_x, post_y, (139, 69, 19))
                    
                    if random.random() < 0.05:
                        r, g, b = wood_color
                        weather = random.uniform(0.8, 1.2)
                        wood_color = (int(r*weather), int(g*weather), int(b*weather))
                    
                    draw.point((post_x, post_y), fill=wood_color)
            
            draw.rectangle((fx, y, fx+8, y+50), outline=(0,0,0), width=1)
            
            draw.polygon((fx, y, fx+4, y-8, fx+8, y), fill=(139,69,19), outline=(0,0,0))
            
            for grain_y in [y-6, y-4, y-2]:
                draw.line((fx+2, grain_y, fx+6, grain_y), fill=(101,67,33), width=1)
        
        # Rails
        rail_positions = [(y+15, y+18), (y+30, y+33)]
        
        for rail_y1, rail_y2 in rail_positions:
            for ry in range(rail_y1, rail_y2):
                for rx in range(0, self.width, 2):
                    rail_color = self.wood_texture(rx, ry, (160, 82, 45))
                    draw.rectangle((rx, ry, rx+2, ry+1), fill=rail_color)
            
            draw.rectangle((0, rail_y1, self.width, rail_y2), outline=(0,0,0), width=1)
    
    def draw_birds(self, draw):
        for x in [100, 250, 400]:
            y = 120
            draw.line((x-8, y, x, y-5), fill=(0,0,0), width=2)
            draw.line((x, y-5, x+8, y), fill=(0,0,0), width=2)
    
    def draw_airplane(self, draw):
        x, y = 350, 100
        draw.ellipse((x, y, x+60, y+15), fill=(192,192,192), outline=(0,0,0), width=2)
        draw.polygon((x+20, y+7, x+40, y+7, x+55, y-15, x+5, y-15), fill=(169,169,169), outline=(0,0,0), width=2)
    
    def draw_city(self, draw):
        for i, (x1, y1, x2, y2) in enumerate([(50, 180, 80, 250), (85, 150, 120, 250), (230, 130, 270, 250)]):
            gray = int(100 + i*30)
            draw.rectangle((x1, y1, x2, y2), fill=(gray, gray, gray), outline=(0,0,0), width=2)
    
    def draw_rain(self, draw):
        for _ in range(80):
            x, y = random.randint(0, self.width), random.randint(0, self.height)
            draw.line((x, y, x-2, y+15), fill=(176,224,230), width=1)
    
    def draw_snow(self, draw):
        for _ in range(100):
            x, y = random.randint(0, self.width), random.randint(0, self.height)
            draw.ellipse((x, y, x+2, y+2), fill=(255,255,255))

# --- New: Simple Text Generator ---
def generate_story(topic):
    # Procedural story generation using random elements + Wikipedia fact
    fact = KnowledgeEngine().search(topic)
    starters = ["Once upon a time", "In a distant land", "Long ago"]
    middles = ["there was a hero who", "a mysterious event happened where", "people discovered that"]
    ends = ["and they lived happily ever after.", "but that's a story for another time.", "leading to great adventures."]
    
    story = f"{random.choice(starters)}, {topic} {random.choice(middles)} {fact[:100]}... {random.choice(ends)}"
    return story

# --- New: Chat with Groq LLM ---
def chat_with_groq(message):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama3-70b-8192",  # Fast and smart
        "messages": [{"role": "user", "content": message}],
        "temperature": 0.7,
        "max_tokens": 500
    }
    response = requests.post(GROQ_CHAT_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        return "Error: Could not get response from Groq."

# --- New: Generate image with Groq Flux.1-schnell ---
def generate_image_with_groq(prompt):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "flux-schnell",
        "prompt": prompt,
        "size": "1024x1024"
    }
    response = requests.post(GROQ_IMAGE_URL, headers=headers, json=payload)
    if response.status_code == 200:
        image_url = response.json()['data'][0]['url']
        img_response = requests.get(image_url)
        return Image.open(io.BytesIO(img_response.content))
    else:
        return None

# --- WEB APP WITH STREAMLIT ---
st.set_page_config(page_title="SmartBot Advanced Web Edition", layout="wide")

st.title("🤖 SmartBot Advanced v27 - Web Edition")
st.markdown("""
⚡ CAPABILITIES:
• Natural chat and conversation
• Spatial relationship understanding (e.g., "dog in brown house" for drawing)
• Resolution control: 480p to 8k (for drawings)
• Knowledge retrieval from Wikipedia with step-by-step reasoning
• Generate simple stories (e.g., "generate story about mountains")
• Play games (e.g., "play guess number")
• Real AI image generation with Flux.1-schnell (e.g., "generate image of a cat in space")

📝 EXAMPLES:
• "Hi, how are you?"
• "Tell me a joke"
• "What is Python programming?"
• "draw a red car on the road at sunset"
• "generate story about a dog"
• "play guess number"
• "generate image of a cartoon cactus on the toilet with a microphone"
""")

# Session state for chat history and game state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'game_active' not in st.session_state:
    st.session_state.game_active = False
if 'secret_number' not in st.session_state:
    st.session_state.secret_number = None

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "image" in message:
            st.image(message["image"])

# Input
prompt = st.chat_input("Type your command...")

resolution = st.selectbox("Resolution (for procedural drawings)", ['480p', '720p', '1080p', '4k', '8k'], index=2)

if prompt:
    # User message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.spinner("Processing..."):
        query_lower = prompt.lower()
        
        image_triggers = ["draw", "create", "show", "render", "make"]
        api_image_triggers = ["generate image", "flux image", "ai image"]
        story_triggers = ["generate story", "tell story", "create story"]
        game_triggers = ["play guess number", "play game"]
        
        is_api_image = any(t in query_lower for t in api_image_triggers)
        is_image = any(t in query_lower for t in image_triggers) and not is_api_image
        is_story = any(t in query_lower for t in story_triggers)
        is_game = any(t in query_lower for t in game_triggers)
        
        if is_api_image:
            desc = prompt.lower().replace("generate image", "").replace("flux image", "").replace("ai image", "").strip()
            img = generate_image_with_groq(desc)
            if img:
                response = f"✓ Flux.1-schnell generated: {desc}"
                st.session_state.messages.append({"role": "assistant", "content": response, "image": img})
                with st.chat_message("assistant"):
                    st.markdown(response)
                    st.image(img)
                    st.download_button("Download Image", img.tobytes(), "flux_image.png", "image/png")
            else:
                response = "Error: Could not generate image. Check API key or quota."
                st.session_state.messages.append({"role": "assistant", "content": response})
                with st.chat_message("assistant"):
                    st.markdown(response)
        
        elif is_image:
            scene = PromptParser().parse(prompt)
            sizes = {'480p': (400, 300), '720p': (640, 480), '1080p': (800, 600), '4k': (800, 600), '8k': (800, 600)}  # Limit size for web, detail controls quality
            width, height = sizes[resolution]
            renderer = AdvancedRenderer(width=width, height=height, resolution=resolution)
            img = renderer.render_scene(scene)
            
            response = f"✓ Rendered! Objects: {', '.join(scene['objects'])} | Time: {scene['time']} | Weather: {scene['weather']}"
            st.session_state.messages.append({"role": "assistant", "content": response, "image": img})
            with st.chat_message("assistant"):
                st.markdown(response)
                st.image(img)
                st.download_button("Download Image", img.tobytes(), "scene.png", "image/png")
        
        elif is_story:
            topic = prompt.lower().replace("generate story about", "").replace("tell story about", "").replace("create story about", "").strip()
            story = generate_story(topic)
            st.session_state.messages.append({"role": "assistant", "content": story})
            with st.chat_message("assistant"):
                st.markdown(story)
        
        elif is_game or st.session_state.game_active:
            if not st.session_state.game_active:
                st.session_state.game_active = True
                st.session_state.secret_number = random.randint(1, 100)
                response = "Game started! I'm thinking of a number between 1 and 100. Guess it! (Type 'quit' to stop)"
            else:
                if query_lower == 'quit':
                    st.session_state.game_active = False
                    st.session_state.secret_number = None
                    response = "Game ended. Type a new command!"
                else:
                    try:
                        guess = int(prompt)
                        if guess < st.session_state.secret_number:
                            response = "Too low! Guess higher."
                        elif guess > st.session_state.secret_number:
                            response = "Too high! Guess lower."
                        else:
                            response = f"Correct! The number was {st.session_state.secret_number}. Great job! Game over."
                            st.session_state.game_active = False
                            st.session_state.secret_number = None
                    except ValueError:
                        response = "Please guess a number (1-100) or 'quit'."
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):
                st.markdown(response)
        
        else:
            # Natural chat with Groq LLM
            answer = chat_with_groq(prompt)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            with st.chat_message("assistant"):
                st.markdown(answer)
