import math
import pygame
from pygame.locals import *
import moderngl
import os
import json
import numba
from array import array


@numba.njit(cache=True)
def linear_interpolation(x0: int, x1: int, p: float) -> float:
    return x0 + (x1 - x0) * p


pygame.init()
pygame.font.init()

pygame.event.set_allowed([QUIT, KEYDOWN, KEYUP])
window = pygame.display.set_mode((1200, 600), DOUBLEBUF | OPENGL)
display = pygame.Surface((1200, 600))
ctx = moderngl.create_context()
pygame.display.set_caption("Byted Space Project")
font = pygame.font.SysFont('Comic Sans MS', 20)
big_font = pygame.font.SysFont('Comic Sans MS', 32)

quad_buffer = ctx.buffer(data=array('f', [
    # position (x, y), uv coords (x, y)
    -1.0, 1.0, 0.0, 0.0,  # topleft
    1.0, 1.0, 1.0, 0.0,  # topright
    -1.0, -1.0, 0.0, 1.0,  # bottomleft
    1.0, -1.0, 1.0, 1.0,  # bottomright
]))

program = ctx.program(vertex_shader="""
#version 330 core

in vec2 vert;
in vec2 texcoord;
out vec2 uvs;

void main() {
    uvs = texcoord;
    gl_Position = vec4(vert, 0.0, 1.0);
}
""", fragment_shader="""
#version 330 core

uniform sampler2D tex;

in vec2 uvs;
out vec4 f_color;

void main() {
    vec2 sample_pos = vec2(uvs.x, uvs.y);
    f_color = vec4(texture(tex, sample_pos).rg, texture(tex, sample_pos).b * 1.5, 1.0);
}
""")
bloom = ctx.program(vertex_shader="""
#version 330 core

in vec2 vert;
in vec2 texcoord;
out vec2 uvs;

void main() {
    uvs = texcoord;
    gl_Position = vec4(vert, 0.0, 1.0);
}
""", fragment_shader="""
#version 330 core

uniform sampler2D tex;
uniform float threshold; // Threshold to determine bright areas
uniform float bloomIntensity; // Intensity of the bloom effect
uniform float blurRadius; // Radius of the blur

in vec2 uvs;
out vec4 f_color;

// Function to calculate Gaussian blur
vec4 gaussianBlur(sampler2D image, vec2 uv, vec2 resolution, float radius) {
    vec4 color = vec4(0.0);
    float totalWeight = 0.0;

    // Gaussian kernel
    for (float x = -radius; x <= radius; x++) {
        for (float y = -radius; y <= radius; y++) {
            vec2 offset = vec2(x, y) / resolution;
            float weight = exp(-(offset.x * offset.x + offset.y * offset.y) * 4.0 * radius);
            color += texture(image, uv + offset) * weight;
            totalWeight += weight;
        }
    }

    return color / totalWeight;
}

void main() {
    // Sample the original image
    vec4 originalColor = texture(tex, uvs);
    
    // Calculate the luminance of the pixel
    float luminance = (originalColor.r + originalColor.g + originalColor.b) / 3.0;
    
    // Check if the pixel is bright enough
    if (luminance > threshold) {
        // Apply bloom effect to bright pixels
        vec4 bloomColor = gaussianBlur(tex, uvs, textureSize(tex, 0), blurRadius) * bloomIntensity;
        
        // Add the bloom color to the original color
        f_color = originalColor + bloomColor;
    } else {
        // Otherwise, just output the original color
        f_color = originalColor;
    }
}
""")

render_object = ctx.vertex_array(program, [(quad_buffer, '2f 2f', 'vert', 'texcoord')])
render_bloom = ctx.vertex_array(bloom, [(quad_buffer, '2f 2f', 'vert', 'texcoord')])


def surf_to_texture(surf):
    tex = ctx.texture(surf.get_size(), 4)
    tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
    tex.swizzle = 'BGRA'
    tex.write(surf.get_view('1'))
    return tex


# Base values ------------------------------------
config = {
    "path": {
        "textures": "textures",
        "locales": "locales",
        "settings": "settings.json"
    },
    "default_settings": {
        "lang": "en_us",
        "fps": 60,
        "bloom": True,
        "chromatic_aberration": True,
        "anti_aliasing": True,
        "other_distortion_effects": True,
        "screen_shake": 1.0,
        "music": 80,
        "sound": 100
    }
}


def load_settings(path):
    if os.path.exists(path):
        with open(path, 'r') as file:
            data = json.load(file)
    else:
        data = config["default_settings"]
        with open(path, 'w') as file:
            json.dump(data, file, indent=4)
    return data


def save_settings(data, path):
    with open(path, 'w') as file:
        json.dump(data, file, indent=4)


settings = load_settings(config["path"]["settings"])

tiles = {
    1: "tiles.",
    2: "tiles.",
    3: "tiles.",
    4: "tiles.",
    5: "tiles.",
    6: "tiles.",
    7: "tiles.",
    8: "tiles.",
    9: "tiles.",
    10: "tiles.",
    11: "tiles.",
    12: "tiles.",
    13: "tiles.",
    14: "tiles.",
    15: "tiles.",
    16: "tiles.",
    17: "tiles."
}

modifiers = {
    # Negative modifiers
    "low_shield": {
        "name": "modifier.low_shield",
        "description": "modifier.low_shield.description",
        "texture": "modifiers.low_shield",
        "incompatible": ["high_shield"],
        "action": "mul",
        "effects": {
            "shield": 0.5
        },
        "DP": -3
    },
    "low_health": {
        "name": "modifier.low_health",
        "description": "modifier.low_health.description",
        "texture": "modifiers.low_health",
        "incompatible": ["high_health"],
        "action": "mul",
        "effects": {
            "health": 0.5
        },
        "DP": -3
    },
    "low_mobility": {
        "name": "modifier.low_mobility",
        "description": "modifier.low_mobility.description",
        "texture": "modifiers.low_mobility",
        "incompatible": ["high_mobility"],
        "action": "mul",
        "effects": {
            "move_speed": 0.6,
            "rotation_speed": 0.6
        },
        "DP": -3
    },
    "low_attack_speed": {
        "name": "modifier.low_attack_speed",
        "description": "modifier.low_attack_speed.description",
        "texture": "modifiers.low_attack_speed",
        "incompatible": ["high_attack_speed"],
        "action": "mul",
        "effects": {
            "attack_speed": 0.6
        },
        "DP": -3
    },
    "low_damage": {
        "name": "modifier.low_damage",
        "description": "modifier.low_damage.description",
        "texture": "modifiers.low_damage",
        "incompatible": ["high_damage"],
        "action": "mul",
        "effects": {
            "damage": 0.6
        },
        "DP": -3
    },
    "high_energy_usage": {
        "name": "modifier.high_energy_usage",
        "description": "modifier.high_energy_usage.description",
        "texture": "modifiers.high_energy_usage",
        "incompatible": ["low_energy_usage"],
        "action": "mul",
        "effects": {
            "energy_usage": 1.5
        },
        "DP": -2
    },
    "low_projectile_speed": {
        "name": "modifier.low_projectile_speed",
        "description": "modifier.low_projectile_speed.description",
        "texture": "modifiers.low_projectile_speed",
        "incompatible": ["high_projectile_speed"],
        "action": "mul",
        "effects": {
            "projectile_speed": 0.5
        },
        "DP": -2
    },
    "high_heating": {
        "name": "modifier.high_heating",
        "description": "modifier.high_heating.description",
        "texture": "modifiers.high_heating",
        "incompatible": ["low_heating"],
        "action": "mul",
        "effects": {
            "heating": 1.5
        },
        "DP": -1
    },
    "low_laser_width": {
        "name": "modifier.low_laser_width",
        "description": "modifier.low_laser_width.description",
        "texture": "modifiers.low_laser_width",
        "incompatible": ["high_laser_width"],
        "action": "mul",
        "effects": {
            "laser_width": 0.7
        },
        "DP": -1
    },
    # Unstable
    "glass_cannon": {
        "name": "modifier.glass_cannon",
        "description": "modifier.glass_cannon.description",
        "texture": "modifiers.glass_cannon",
        "incompatible": [],
        "action": "mul",
        "effects": {
            "damage": 2,
            "damage_gain": 2
        },
        "DP": 0
    },
    "regeneration_swap": {
        "name": "modifier.regeneration_swap",
        "description": "modifier.regeneration_swap.description",
        "texture": "modifiers.regeneration_swap",
        "incompatible": [],
        "action": "set",
        "effects": {
            "shield_regeneration": 0,
            "health_regeneration": 1
        },
        "DP": 0
    },
    "acceleration": {
        "name": "modifier.acceleration",
        "description": "modifier.acceleration.description",
        "texture": "modifiers.acceleration",
        "incompatible": [],
        "action": "mul",
        "effects": {
            "can_shoot_while_rotating": 0,
            "movement_speed": 1.5
        },
        "DP": 0
    },
    "overclock": {
        "name": "modifier.overclock",
        "description": "modifier.overclock.description",
        "texture": "modifiers.overclock",
        "incompatible": [],
        "action": "mul",
        "effects": {
            "heating": 3,
            "overheat_duration": 1.5,
            "attack_speed": 1.5
        },
        "DP": 0
    },
    # Positive modifiers
    "high_shield": {
        "name": "modifier.high_shield",
        "description": "modifier.high_shield.description",
        "texture": "modifiers.high_shield",
        "incompatible": ["low_shield"],
        "action": "mul",
        "effects": {
            "shield": 1.8
        },
        "DP": 3
    },
    "high_health": {
        "name": "modifier.high_health",
        "description": "modifier.high_health.description",
        "texture": "modifiers.high_health",
        "incompatible": ["low_health"],
        "action": "mul",
        "effects": {
            "health": 1.8
        },
        "DP": 3
    },
    "high_mobility": {
        "name": "modifier.high_mobility",
        "description": "modifier.high_mobility.description",
        "texture": "modifiers.high_mobility",
        "incompatible": ["low_mobility"],
        "action": "mul",
        "effects": {
            "move_speed": 1.5,
            "rotation_speed": 1.5
        },
        "DP": 3
    },
    "high_attack_speed": {
        "name": "modifier.high_attack_speed",
        "description": "modifier.high_attack_speed.description",
        "texture": "modifiers.high_attack_speed",
        "incompatible": ["low_attack_speed"],
        "action": "mul",
        "effects": {
            "attack_speed": 1.5
        },
        "DP": 3
    },
    "high_damage": {
        "name": "modifier.high_damage",
        "description": "modifier.high_damage.description",
        "texture": "modifiers.high_damage",
        "incompatible": ["low_damage"],
        "action": "mul",
        "effects": {
            "damage": 1.5
        },
        "DP": 3
    },
    "low_energy_usage": {
        "name": "modifier.low_energy_usage",
        "description": "modifier.low_energy_usage.description",
        "texture": "modifiers.low_energy_usage",
        "incompatible": ["high_energy_usage"],
        "action": "mul",
        "effects": {
            "energy_usage": 0.5
        },
        "DP": 2
    },
    "high_projectile_speed": {
        "name": "modifier.high_projectile_speed",
        "description": "modifier.high_projectile_speed.description",
        "texture": "modifiers.high_projectile_speed",
        "incompatible": ["low_projectile_speed"],
        "action": "mul",
        "effects": {
            "projectile_speed": 1.5
        },
        "DP": 2
    },
    "low_heating": {
        "name": "modifier.low_heating",
        "description": "modifier.low_heating.description",
        "texture": "modifiers.low_heating",
        "incompatible": ["high_heating"],
        "action": "mul",
        "effects": {
            "heating": 0.8
        },
        "DP": 1
    },
    "high_laser_width": {
        "name": "modifier.high_laser_width",
        "description": "modifier.high_laser_width.description",
        "texture": "modifiers.high_laser_width",
        "incompatible": ["low_laser_width"],
        "action": "mul",
        "effects": {
            "laser_width": 1.2
        },
        "DP": 1
    },
}


# Locales ------------------------------------
def load_locales(directory):
    loaded = {}
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            locale_name = os.path.splitext(filename)[0]
            with open(os.path.join(directory, filename), 'r', encoding='utf-8') as file:
                data = json.load(file)
                loaded[locale_name] = data
    return loaded


def get_translated(lang, path):
    if lang in locales and path in locales[lang]:
        return locales[lang][path]
    else:
        return "404"


locales = load_locales(config["path"]["locales"])


# Textures ------------------------------------
def load_textures(directory):
    loaded = {}

    empty_texture = pygame.Surface((32, 32))
    empty_texture.fill((0, 0, 0))
    loaded['__empty__'] = empty_texture

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.png'):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, directory)
                relative_path = relative_path.replace(os.path.sep, '.')
                texture_key = os.path.splitext(relative_path)[0]
                texture = pygame.image.load(file_path).convert_alpha()
                loaded[texture_key] = texture

    return loaded


def get_texture(path):
    if path in textures:
        return textures[path]
    else:
        return textures['__empty__']


textures = load_textures(config["path"]["textures"])


# Menu ------------------------------------
class Menu:
    def __init__(self):
        self.sin_i = 0
        self.selected = 0
        self.dynamic_cursor_y = 0
        self.pointer_texture = get_texture("other.pointer")
        self.current_menu = "main"
        self.menus = {
            "main": {
                "name": "game.name",
                0: {
                    "name": "menu.play",
                    "action": "goto",
                    "goto": "play"
                },
                1: {
                    "name": "menu.options",
                    "action": "goto",
                    "goto": "options"
                },
                2: {
                    "name": "menu.quit",
                    "action": "quit"
                }
            },
            "options": {
                "name": "menu.options",
                0: {
                    "name": "menu.back",
                    "action": "goto&save",
                    "goto": "main"
                },
                1: {
                    "name": "menu.options.music",
                    "action": "edit",
                    "min": 0,
                    "max": 200,
                    "step": 1,
                    "target": "music"
                },
                2: {
                    "name": "menu.options.sounds",
                    "action": "edit",
                    "min": 0,
                    "max": 200,
                    "step": 1,
                    "target": "sounds"
                },
                3: {
                    "name": "menu.options.language",
                    "action": "language"
                },
                4: {
                    "name": "menu.options.fps",
                    "action": "edit",
                    "min": 30,
                    "max": 240,
                    "step": 30,
                    "target": "sounds"
                },
                5: {
                    "name": "menu.options.bloom",
                    "action": "switch",
                    "target": "bloom"
                },
                6: {
                    "name": "menu.options.chromatic_aberration",
                    "action": "switch",
                    "target": "chromatic_aberration"
                },
                7: {
                    "name": "menu.options.anti_aliasing",
                    "action": "switch",
                    "target": "anti_aliasing"
                },
                8: {
                    "name": "menu.options.other_distortion_effects",
                    "action": "switch",
                    "target": "other_distortion_effects"
                },
                9: {
                    "name": "menu.options.screen_shake",
                    "action": "edit",
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.1,
                    "target": "screen_shake"
                }
            },
            "play": {
                "name": "menu.play",
                0: {
                    "name": "menu.back",
                    "action": "goto",
                    "goto": "main"
                },
                1: {
                    "name": "menu.play.connect",
                    "action": "-"
                }
            }
        }

    def update(self):
        self.sin_i += 0.05
        if self.sin_i >= 360:
            self.sin_i -= 360
        self.dynamic_cursor_y = linear_interpolation(self.dynamic_cursor_y, self.selected * 30 + 58, 0.1)

    def render(self, x, y):
        display.blit(self.pointer_texture, (x + (math.sin(self.sin_i) * 5), y + self.dynamic_cursor_y))
        for i in range(len(self.menus[self.current_menu]) - 1):
            c = (255, 255, 255)
            if i == self.selected:
                c = (255, 255, 0)
            display.blit(
                font.render(get_translated(settings["lang"], self.menus[self.current_menu][i]["name"]),
                            settings["anti_aliasing"], c), (x + 30, y + 50 + (i * 30)))
            if self.menus[self.current_menu][i]["action"] in ("edit", "switch", "language"):
                display.blit(font.render("<", settings["anti_aliasing"], c), (x + 500, y + 50 + (i * 30)))
                display.blit(font.render(">", settings["anti_aliasing"], c), (x + 700, y + 50 + (i * 30)))
                if self.menus[self.current_menu][i]["action"] == "language":
                    text_width, text_height = font.size(get_translated(settings["lang"], "__name__"))
                    display.blit(
                        font.render(get_translated(settings["lang"], "__name__"), settings["anti_aliasing"], c),
                        (x + 600 - (text_width / 2), y + 50 + (i * 30)))
                if self.menus[self.current_menu][i]["action"] == "switch":
                    a = {True: "menu.enabled", False: "menu.disabled"}[
                        settings[self.menus[self.current_menu][i]["target"]]]
                    text_width, text_height = font.size(get_translated(settings["lang"], a))
                    display.blit(font.render(get_translated(settings["lang"], a), settings["anti_aliasing"], c),
                                 (x + 600 - (text_width / 2), y + 50 + (i * 30)))
        if self.menus[self.current_menu]["name"] is not None:
            display.blit(
                big_font.render(get_translated(settings["lang"], self.menus[self.current_menu]["name"]),
                                settings["anti_aliasing"], (255, 255, 255)), (x, y))

    def up(self):
        self.selected -= 1
        if self.selected < 0:
            self.selected = len(self.menus[self.current_menu]) - 2

    def down(self):
        self.selected += 1
        if self.selected > len(self.menus[self.current_menu]) - 2:
            self.selected = 0

    def apply(self):
        global running
        if self.menus[self.current_menu][self.selected]["action"] == "goto":
            self.current_menu = self.menus[self.current_menu][self.selected]["goto"]
            self.selected = 0
        elif self.menus[self.current_menu][self.selected]["action"] == "goto&save":
            self.current_menu = self.menus[self.current_menu][self.selected]["goto"]
            save_settings(settings, config["path"]["settings"])
            self.selected = 0
        elif self.menus[self.current_menu][self.selected]["action"] == "quit":
            running = False

    def next(self):
        global settings
        if self.menus[self.current_menu][self.selected]["action"] == "language":
            i = list(locales.keys()).index(settings["lang"]) + 1
            if i > len(locales) - 1:
                i = 0
            settings["lang"] = list(locales.keys())[i]
        elif self.menus[self.current_menu][self.selected]["action"] == "switch":
            settings[self.menus[self.current_menu][self.selected]["target"]] = not settings[
                self.menus[self.current_menu][self.selected]["target"]]

    def previous(self):
        global settings
        if self.menus[self.current_menu][self.selected]["action"] == "language":
            settings["lang"] = list(locales.keys())[list(locales.keys()).index(settings["lang"]) - 1]
        elif self.menus[self.current_menu][self.selected]["action"] == "switch":
            settings[self.menus[self.current_menu][self.selected]["target"]] = not settings[
                self.menus[self.current_menu][self.selected]["target"]]


# Init ------------------------------------
clock = pygame.time.Clock()
screen = "menu"
menu = Menu()
if __name__ == "__main__":
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_w:
                    menu.up()
                elif event.key == K_s:
                    menu.down()
                elif event.key == K_a:
                    menu.previous()
                elif event.key == K_d:
                    menu.next()
                elif event.key == K_RETURN:
                    menu.apply()
        if screen == "menu":
            menu.update()
        display.fill((10, 10, 10))
        if screen == "menu":
            menu.render(100, 100)

        frame_tex = surf_to_texture(display)
        frame_tex.use(0)
        program['tex'] = 0
        render_object.render(mode=moderngl.TRIANGLE_STRIP)
        if settings["bloom"]:
            bloom["threshold"] = 0.0
            bloom["bloomIntensity"] = 0.8
            bloom["blurRadius"] = 5.0
            render_bloom.render(mode=moderngl.TRIANGLE_STRIP)

        pygame.display.flip()
        frame_tex.release()
        clock.tick(60)

    pygame.quit()
