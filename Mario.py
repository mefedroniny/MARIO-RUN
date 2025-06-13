import pygame
import random
import sys

pygame.init()
pygame.mixer.init()

# Spustitelne okno s hornim barem
WIDTH, HEIGHT = 1280, 720
is_fullscreen = False
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Mario Run")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GRAY = (180, 180, 180)
font = pygame.font.SysFont(None, 40)

MENU = 'menu'
SETTINGS = 'settings'
PLAYING = 'playing'
current_state = MENU

DIFFICULTIES = {
    'Lehká': {'scroll_speed': 3, 'enemy_freq': 90},
    'Střední': {'scroll_speed': 5, 'enemy_freq': 60},
    'Těžká': {'scroll_speed': 7, 'enemy_freq': 40},
}
current_difficulty = 'Střední'

def draw_button(text, center_x, y, w, h, action=None):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    x = center_x - w // 2
    rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(screen, GRAY if rect.collidepoint(mouse) else WHITE, rect)
    pygame.draw.rect(screen, BLACK, rect, 2)
    text_surf = font.render(text, True, BLACK)
    screen.blit(text_surf, (x + (w - text_surf.get_width()) // 2, y + (h - text_surf.get_height()) // 2))
    if rect.collidepoint(mouse) and click[0] == 1 and action:
        pygame.time.delay(150)
        action()

def start_game():
    global current_state
    current_state = PLAYING

def open_settings():
    global current_state
    current_state = SETTINGS

def quit_game():
    pygame.quit()
    sys.exit()

def set_difficulty(name):
    global current_difficulty, current_state
    current_difficulty = name
    current_state = MENU

def toggle_fullscreen():
    global screen, is_fullscreen, WIDTH, HEIGHT
    is_fullscreen = not is_fullscreen
    if is_fullscreen:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        info = pygame.display.Info()
        WIDTH, HEIGHT = info.current_w, info.current_h
    else:
        WIDTH, HEIGHT = 1280, 720
        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)

def main():
    global WIDTH, HEIGHT, screen
    pygame.mixer.music.load('mariotheme.ogg')
    pygame.mixer.music.set_volume(1.0)
    pygame.mixer.music.play(-1)

    screen_width, screen_height = WIDTH, HEIGHT
    ground_level = screen_height - 50
    clock = pygame.time.Clock()

    background = pygame.image.load('background.png')
    background = pygame.transform.scale(background, (screen_width, screen_height))

    class Mario(pygame.sprite.Sprite):
        def __init__(self):
            super().__init__()
            original_sprite = pygame.image.load('mariosprite.png')
            scaled_sprite = pygame.transform.scale(original_sprite, (540, 220))
            self.running_frames = [
                scaled_sprite.subsurface((0, 0, 180, 220)),
                scaled_sprite.subsurface((180, 0, 180, 220)),
                scaled_sprite.subsurface((360, 0, 180, 220))
            ]
            self.running_frames = [pygame.transform.scale(f, (60, 80)) for f in self.running_frames]
            self.current_frame = 0
            self.animation_timer = 0
            self.image = self.running_frames[0]
            self.rect = self.image.get_rect()
            self.rect.x = 100
            self.rect.bottom = ground_level
            self.rect.inflate_ip(4, 4)  # zvětší hitbox o trochu
            self.velocity_y = 0
            self.jump_count = 0
            self.max_jumps = 2
            self.is_jumping = False
            self.invincibility_timer = 0
            self.is_invincible = False

        def update(self):
            self.animation_timer += 1
            if self.animation_timer >= 5:
                self.current_frame = (self.current_frame + 1) % len(self.running_frames)
                self.image = self.running_frames[self.current_frame]
                self.animation_timer = 0
            self.velocity_y += 0.5
            self.rect.y += self.velocity_y
            if self.rect.bottom >= ground_level:
                self.rect.bottom = ground_level
                self.velocity_y = 0
                self.jump_count = 0
                self.is_jumping = False
            if self.is_invincible:
                self.invincibility_timer -= 1
                if self.invincibility_timer <= 0:
                    self.is_invincible = False
                    self.max_jumps = 2

        def advanced_jump(self):
            if self.jump_count < self.max_jumps:
                jump_sound.play()
                self.velocity_y = -12
                self.jump_count += 1
                self.is_jumping = True

        def reset(self):
            self.rect.x = 100
            self.rect.bottom = ground_level
            self.velocity_y = 0
            self.jump_count = 0
            self.is_jumping = False
            self.current_frame = 0
            self.animation_timer = 0
            self.is_invincible = False
            self.max_jumps = 2

    class Obstacle(pygame.sprite.Sprite):
        def __init__(self, typ):
            super().__init__()
            if typ == 'pipe':
                self.image = pygame.image.load('pipemario.png')
                self.image = pygame.transform.scale(self.image, (45, 75))  # mírně zmenšená
                self.speed = DIFFICULTIES[current_difficulty]['scroll_speed']
            else:
                self.image = pygame.image.load('goomba.png')
                self.image = pygame.transform.scale(self.image, (40, 40))
                self.speed = DIFFICULTIES[current_difficulty]['scroll_speed'] + 1
            self.rect = self.image.get_rect()
            self.rect.x = screen_width
            self.rect.bottom = ground_level

        def update(self):
            self.rect.x -= self.speed
            if self.rect.right < 0:
                self.kill()

    class PowerUp(pygame.sprite.Sprite):
        def __init__(self, typ, ground_level):
            super().__init__()
            self.typ = typ
            if typ == 'coin':
                self.image = pygame.image.load('coin.png')
                self.image = pygame.transform.scale(self.image, (30, 30))
            else:
                self.image = pygame.image.load('star.png')
                self.image = pygame.transform.scale(self.image, (40, 40))
            self.rect = self.image.get_rect()
            self.rect.x = screen_width
            max_jump_height = 150
            self.rect.bottom = ground_level - random.randint(0, max_jump_height)
            self.speed = 5

        def update(self):
            self.rect.x -= self.speed
            if self.rect.right < 0:
                self.kill()

    jump_sound = pygame.mixer.Sound('mariojump.ogg')
    jump_sound.set_volume(0.3)
    coin_sound = pygame.mixer.Sound('coin.ogg')
    coin_sound.set_volume(0.3)
    game_over_sound = pygame.mixer.Sound('mariogameover.ogg')
    star_sound = pygame.mixer.Sound('star.ogg')

    all_sprites = pygame.sprite.Group()
    obstacles = pygame.sprite.Group()
    power_ups = pygame.sprite.Group()
    mario = Mario()
    all_sprites.add(mario)

    score = 0
    coins = 0
    game_over = False
    spawn_timer = 0
    power_timer = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    toggle_fullscreen()
                if game_over:
                    if event.key == pygame.K_r:
                        game_over = False
                        score = 0
                        coins = 0
                        mario.reset()
                        obstacles.empty()
                        power_ups.empty()
                        pygame.mixer.music.play(-1)
                    elif event.key == pygame.K_f:
                        return
                    elif event.key == pygame.K_p:
                        pygame.quit()
                        sys.exit()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] and not game_over:
            mario.advanced_jump()

        if not game_over:
            spawn_timer += 1
            if spawn_timer >= DIFFICULTIES[current_difficulty]['enemy_freq']:
                obstacle = Obstacle(random.choice(['pipe', 'goomba']))
                all_sprites.add(obstacle)
                obstacles.add(obstacle)
                spawn_timer = 0

            power_timer += 1
            if power_timer >= 120:
                p = PowerUp(random.choice(['coin', 'star']), ground_level)
                all_sprites.add(p)
                power_ups.add(p)
                power_timer = 0

            all_sprites.update()

            for o in obstacles:
                if mario.rect.colliderect(o.rect) and not mario.is_invincible:
                    game_over_sound.play()
                    game_over = True

            for p in power_ups:
                if mario.rect.colliderect(p.rect):
                    if p.typ == 'coin':
                        coins += 1
                        coin_sound.play()
                    else:
                        mario.is_invincible = True
                        mario.invincibility_timer = 180
                        mario.max_jumps = 3
                        star_sound.play()
                    p.kill()

            for o in obstacles:
                if o.rect.right < mario.rect.left:
                    score += 1

        screen.blit(pygame.transform.scale(background, (WIDTH, HEIGHT)), (0, 0))
        all_sprites.draw(screen)

        f = pygame.font.Font(None, 36)
        screen.blit(f.render(f"Score: {score}", True, BLACK), (10, 10))
        screen.blit(f.render(f"Coins: {coins}", True, BLACK), (10, 50))

        if game_over:
            pygame.mixer.music.stop()
            screen.blit(pygame.font.Font(None, 74).render("Game Over", True, RED), (WIDTH // 2 - 150, HEIGHT // 2 - 100))
            screen.blit(f.render("Zmáčkni R pro restart hry", True, BLACK), (WIDTH // 2 - 100, HEIGHT // 2))
            screen.blit(f.render("Zmáčkni F Menu", True, BLACK), (WIDTH // 2 - 100, HEIGHT // 2 + 40))
            screen.blit(f.render("Zmáčkni P pro odchod na plochu", True, BLACK), (WIDTH // 2 - 100, HEIGHT // 2 + 80))

        pygame.display.flip()
        clock.tick(60)

while True:
    screen.fill(WHITE)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.VIDEORESIZE:
            WIDTH, HEIGHT = event.w, event.h
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                toggle_fullscreen()

    center_x = WIDTH // 2

    if current_state == MENU:
        draw_button("Hrát", center_x, 150, 200, 50, start_game)
        draw_button("Nastavení", center_x, 230, 200, 50, open_settings)
        draw_button("Ukončit", center_x, 310, 200, 50, quit_game)
    elif current_state == SETTINGS:
        y = 150
        for name in DIFFICULTIES:
            draw_button(name, center_x, y, 200, 50, lambda n=name: set_difficulty(n))
            y += 80
    elif current_state == PLAYING:
        main()
        current_state = MENU

    pygame.display.flip()
    pygame.time.Clock().tick(60)