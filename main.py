import pygame
import random
from map import Map, TILE_SIZE

pygame.init()
screen_width = 910
screen_height = 560
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Arctic Shooter")
clock = pygame.time.Clock()
game_map = Map("maps/tilemap.tmx")
offset_x = 0
score = 0

moving_left = False
moving_right = False
shoot = False
# colours
rgb = (135, 206, 250)
RED = (255, 0, 0)
# game variables
GRAVITY = 0.75
game_over = False

# loading images
background_image = pygame.image.load("graphics/blue_land_ok.png").convert()
bullet_image = pygame.image.load(f"graphics/bullet.png").convert_alpha()
bullet_image = pygame.transform.scale(
    bullet_image, (int(bullet_image.get_width() / 1.5), bullet_image.get_height() / 1.5)
)
live_heart = pygame.image.load(f"graphics/live_heart.png").convert_alpha()
live_heart = pygame.transform.scale(
    live_heart, (int(live_heart.get_width() / 20), live_heart.get_height() / 20)
)


def draw_background():
    screen.blit(background_image, (0, 0))


def draw_health(health, max_health, x, y):
    hearts = max_health // 30
    for i in range(hearts):
        if health > i * 30:
            screen.blit(live_heart, (x + i * live_heart.get_width(), y))


def save_score(final_score, final_time):
    with open("scores.txt", "a") as file:
        file.write(f"Score: {final_score}, Time: {final_time}s\n")


def get_last_scores():
    try:
        with open("scores.txt", "r") as file:
            lines = file.readlines()
            cleaned_lines = [line.strip() for line in lines]
            return (
                cleaned_lines[-3:-1] if len(cleaned_lines) >= 3 else cleaned_lines[:-1]
            )
    except FileNotFoundError:
        return []


class Character(pygame.sprite.Sprite):
    def __init__(self, character_type, x, y, scale, speed, ammo):
        pygame.sprite.Sprite.__init__(self)
        self.alive = True
        self.health = 90
        self.max_health = self.health
        self.character_type = character_type
        self.speed = speed
        self.direction = 1
        self.jump = False
        self.velocity_y = 0
        self.in_air = True
        self.flip = False
        self.shoot_cooldown = 0
        self.ammo = ammo
        self.start_ammo = ammo
        self.hitbox = pygame.Rect(0, 0, 0, 0)
        self.animation_list = []
        temp_list = []
        self.index = 0
        self.action = 0
        self.update_time = pygame.time.get_ticks()
        # enemy variables
        self.move_counter = 0
        self.idling = False
        self.idling_counter = 0
        self.vision = pygame.Rect(0, 0, 150, 20)
        for i in range(4):
            character_image = pygame.image.load(
                f"graphics/{self.character_type}/idle/{i}.png"
            ).convert_alpha()
            character_image = pygame.transform.scale(
                character_image,
                (
                    int(character_image.get_width() / scale),
                    character_image.get_height() / scale,
                ),
            )
            temp_list.append(character_image)
        self.animation_list.append(temp_list)

        temp_list = []
        for i in range(17):
            character_image = pygame.image.load(
                f"graphics/{self.character_type}/run_shoot/{i}.png"
            ).convert_alpha()
            character_image = pygame.transform.scale(
                character_image,
                (
                    int(character_image.get_width() / scale),
                    character_image.get_height() / scale,
                ),
            )
            temp_list.append(character_image)
        self.animation_list.append(temp_list)

        temp_list = []
        for i in range(13):
            character_image = pygame.image.load(
                f"graphics/{self.character_type}/jump/{i}.png"
            ).convert_alpha()
            character_image = pygame.transform.scale(
                character_image,
                (
                    int(character_image.get_width() / scale),
                    character_image.get_height() / scale,
                ),
            )
            temp_list.append(character_image)
        self.animation_list.append(temp_list)

        temp_list = []
        for i in range(19):
            character_image = pygame.image.load(
                f"graphics/{self.character_type}/death/{i}.png"
            ).convert_alpha()
            character_image = pygame.transform.scale(
                character_image,
                (
                    int(character_image.get_width() / scale),
                    character_image.get_height() / scale,
                ),
            )
            temp_list.append(character_image)
        self.animation_list.append(temp_list)
        self.image = self.animation_list[self.index][self.action]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def set_hitbox(self, width_reduction, height_reduction, x_offset, y_offset):
        new_width = self.rect.width - width_reduction
        new_height = self.rect.height - height_reduction

        if self.flip:
            center_x = self.rect.centerx - new_width // 2 - x_offset
        else:
            center_x = self.rect.centerx - new_width // 2 + x_offset

        center_y = self.rect.centery - new_height // 2 + y_offset
        self.hitbox = pygame.Rect(center_x, center_y, new_width, new_height)
        self.hitbox = pygame.Rect(center_x, center_y, new_width, new_height)

    def update_animation(self):
        animation_time = 20
        self.image = self.animation_list[self.action][self.index]
        if pygame.time.get_ticks() - self.update_time > animation_time:
            self.update_time = pygame.time.get_ticks()
            self.index = self.index + 1
        if self.index >= len(self.animation_list[self.action]):
            if self.action == 3:
                self.index = len(self.animation_list[self.action]) - 1
            else:
                self.index = 0

    def update_action(self, new_action):
        if new_action != self.action:
            self.action = new_action
            self.index = 0
            self.update_time = pygame.time.get_ticks()

    def draw(self):
        screen.blit(
            pygame.transform.flip(self.image, self.flip, False),
            (round(self.rect.x - offset_x), round(self.rect.y)),
        )
        # drawing hitbox
        # pygame.draw.rect(
        #     screen,
        #     (0, 255, 0),
        #     pygame.Rect(
        #         self.hitbox.x - offset_x ,
        #         self.hitbox.y  ,
        #         self.hitbox.width,
        #         self.hitbox.height
        #     ),
        #     2
        # )

    def move(self, moving_left, moving_right):
        global offset_x
        global game_over, elapsed_time
        dx = 0
        dy = 0
        on_ground = False

        if moving_left:
            dx = -self.speed
            self.flip = True
            self.direction = -1
        elif moving_right:
            dx = self.speed
            self.flip = False
            self.direction = 1

        # jump
        if self.jump and not self.in_air:
            self.velocity_y = -13  # power of jumping
            self.jump = False
            self.in_air = True

        # gravity
        self.velocity_y += GRAVITY
        if self.velocity_y > 10:  # limit of falling speed
            self.velocity_y = 10
        dy += self.velocity_y

        # collisions with platforms
        for tile in game_map.collision_tiles:
            if tile.rect.colliderect(
                self.hitbox.x + dx, self.hitbox.y, self.hitbox.width, self.hitbox.height
            ):
                # horizontal movement
                if dx > 0:  # left
                    dx = tile.rect.left - self.hitbox.right
                elif dx < 0:  # right
                    dx = tile.rect.right - self.hitbox.left

            if tile.rect.colliderect(
                self.hitbox.x, self.hitbox.y + dy, self.hitbox.width, self.hitbox.height
            ):
                # falling
                if self.velocity_y > 0:
                    dy = tile.rect.top - self.hitbox.bottom
                    self.in_air = False
                # jump
                elif self.velocity_y < 0:
                    dy = tile.rect.bottom - self.hitbox.top
                    self.velocity_y = 0

        if not any(
            tile.rect.colliderect(
                self.hitbox.x, self.hitbox.y + 1, self.hitbox.width, self.hitbox.height
            )
            for tile in game_map.collision_tiles
        ):
            self.in_air = True

        if self.character_type == "main_character":
            max_offset_x = max(0, game_map.map_width - screen.get_width())
            offset_x = max(
                0,
                min((self.rect.centerx - screen.get_width() // 2 + 200), max_offset_x),
            )

            if self.rect.left <= 0:
                self.rect.left = 0

            if offset_x >= max_offset_x:
                offset_x = max_offset_x
                if self.rect.right >= game_map.map_width:
                    self.rect.right = game_map.map_width
            if self.rect.top > screen.get_height():
                self.health = 0

            if (
                self.health <= 0 or self.rect.right >= game_map.map_width
            ) and not game_over:
                game_over = True
                end_time = pygame.time.get_ticks()
                elapsed_time = (end_time - start_time) // 1000

                save_score(score, elapsed_time)

        self.rect.x += dx
        self.rect.y += dy

        self.hitbox.x = self.rect.x + (self.rect.width - self.hitbox.width) // 2
        self.hitbox.y = self.rect.y + (self.rect.height - self.hitbox.height) // 2

    def shoot(self, x_offset, y_offset):
        if self.shoot_cooldown == 0 and self.ammo > 0:
            self.shoot_cooldown = 20

            bullet_x = self.rect.centerx + x_offset * self.direction
            bullet_y = self.rect.centery + y_offset

            bullet = Bullet(bullet_x, bullet_y, self.direction, self)
            bullet_group.add(bullet)
            self.ammo -= 1

    def heuristic_algorithm(self):
        if self.alive and player.alive:
            self.vision.center = (
                self.rect.centerx + 100 * self.direction,
                self.rect.centery,
            )
            # pygame.draw.rect(screen, RED, pygame.Rect(self.vision.x - offset_x, self.vision.y, self.vision.width, self.vision.height))
            if not self.idling and random.randint(1, 300) == 11:
                self.update_action(0)
                self.idling = True
                self.idling_counter = 30

            if self.idling:
                self.update_action(0)
                self.idling_counter -= 1
                if self.idling_counter <= 0:
                    self.idling = False
            else:
                if self.vision.colliderect(player.hitbox):
                    distance = abs(self.rect.centerx - player.rect.centerx)
                    # print(f"Player detected! Distance: {distance}")
                    self.shoot_cooldown_max = max(20, 50 + distance // 1.5)
                    # print(f"Adjusted shoot cooldown max: {self.shoot_cooldown_max}")
                    if self.shoot_cooldown == 0:
                        self.shoot(20, 0)
                        self.shoot_cooldown = self.shoot_cooldown_max

                if not self.idling:
                    if self.direction == 1:
                        self.move(False, True)
                    elif self.direction == -1:
                        self.move(True, False)

                    self.update_action(1)
                    self.move_counter += 1
                    if self.move_counter > TILE_SIZE:
                        self.direction *= -1
                        self.move_counter = 0

            if self.shoot_cooldown > 0:
                self.shoot_cooldown -= 1
                # print(f"[DEBUG] Shoot cooldown: {self.shoot_cooldown}")

    def update(self):
        self.update_animation()
        self.check_alive()
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def check_alive(self):
        if self.health <= 0:
            self.health = 0
            self.speed = 0
            self.alive = False
            self.update_action(3)


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, shooter):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 10
        self.image = bullet_image
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction
        self.shooter = shooter
        if direction == -1:
            self.image = pygame.transform.rotate(self.image, 180)

    def update(self):
        self.rect.x += self.direction * self.speed
        if self.rect.right < 0 or self.rect.left > screen_width + offset_x:
            self.kill()

        if pygame.sprite.collide_rect(self, player) and player.alive:
            if self.shooter != player:
                if player.hitbox.colliderect(self.rect):
                    player.health -= 30
                    self.kill()
        for enemy in enemies:
            if pygame.sprite.collide_rect(self, enemy) and enemy.alive:
                if self.shooter != enemy:
                    if enemy.hitbox.colliderect(self.rect):
                        enemy.health -= 90
                        self.kill()
                        if enemy.health <= 0:
                            global score
                            score += 10


bullet_group = pygame.sprite.Group()
enemies = pygame.sprite.Group()
for spawn_point in game_map.enemy_spawn_points:
    x, y = spawn_point
    enemy = Character("enemy", x, y, scale=5, speed=3, ammo=100)
    enemies.add(enemy)

player = Character("main_character", 200, 200, 4, 3, 100)


def reset_game():
    global game_over, player, enemies, bullet_group, score, start_time, elapsed_time
    game_over = False
    player = Character("main_character", 200, 200, 4, 3, 100)
    enemies.empty()
    for spawn_point in game_map.enemy_spawn_points:
        x, y = spawn_point
        enemy = Character("enemy", x, y, 5, 3, 100)
        enemies.add(enemy)
    bullet_group.empty()
    score = 0
    elapsed_time = 0
    start_time = pygame.time.get_ticks()

running=True
game_started=False

while running:
    if not game_started:
        screen.blit(background_image, (0, 0))
        font = pygame.font.Font(None, 80)
        start_text = font.render("PRESS ENTER TO START", True, (249, 198, 207))
        exit_text = font.render("PRESS ESC TO EXIT", True, (249, 198, 207))
        start_text_rect = start_text.get_rect(center=(screen_width // 2, screen_height // 2 - 50))
        exit_text_rect = exit_text.get_rect(center=(screen_width // 2, screen_height // 2 + 50))
        screen.blit(start_text, start_text_rect)
        screen.blit(exit_text, exit_text_rect)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:  # ENTER
                    game_started = True
                    start_time = pygame.time.get_ticks()
                if event.key == pygame.K_ESCAPE:
                    running = False

    elif game_over:
        screen.blit(background_image, (0, 0))

        font1 = pygame.font.Font(None, 100)
        font2 = pygame.font.Font(None, 60)
        font3 = pygame.font.Font(None, 80)
        font4 = pygame.font.Font(None, 40)
        text = font1.render("GAME OVER", True, (249, 198, 207))
        text_rect = text.get_rect(
            center=(screen.get_width() // 2, screen.get_height() // 2 - 50)
        )
        screen.blit(text, text_rect)

        score_text = font3.render(f"Score: {score}", True, (228, 129, 147))
        score_text_rect = score_text.get_rect(
            center=(screen.get_width() // 2, screen.get_height() // 2 + 30)
        )
        screen.blit(score_text, score_text_rect)

        time_text = font3.render(f"Time: {elapsed_time} s", True, (228, 129, 147))
        time_text_rect = time_text.get_rect(
            center=(screen.get_width() // 2, screen.get_height() // 2 + 80)
        )
        screen.blit(time_text, time_text_rect)

        restart_text = font2.render("Press R to Restart", True, (249, 198, 207))
        restart_text_rect = restart_text.get_rect(
            center=(screen.get_width() // 2, screen.get_height() // 2 + 150)
        )
        screen.blit(restart_text, restart_text_rect)

        restart_text = font4.render("Previous scores:", True, (255, 255, 255))
        restart_text_rect = restart_text.get_rect(
            center=(screen.get_width() // 2, screen.get_height() // 2 + 190)
        )
        screen.blit(restart_text, restart_text_rect)
        last_scores = get_last_scores()
        y_offset = 220
        for line in last_scores:
            last_score_text = font4.render(line, True, (255, 255, 255))
            last_score_rect = last_score_text.get_rect(
                center=(screen.get_width() // 2, screen.get_height() // 2 + y_offset)
            )
            screen.blit(last_score_text, last_score_rect)
            y_offset += 30
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    reset_game()
                if event.key == pygame.K_ESCAPE:
                    running = False

    else:
        draw_background()
        player.draw()
        player.update()
        game_map.draw_map(offset_x)
        player.set_hitbox(70, 40, 0, 0)
        player.draw()
        draw_health(player.health, player.max_health, 10, 10)
        player.update()
        for enemy in enemies:
            enemy.heuristic_algorithm()
            enemy.set_hitbox(80, 10, -20, 0)
            enemy.update()
            enemy.draw()

        bullet_group.update()
        for bullet in bullet_group:
            screen.blit(bullet.image, (bullet.rect.x - offset_x, bullet.rect.y))

        if player.alive:
            if shoot:
                player.shoot(45, -16)
            if moving_left or moving_right:
                player.update_action(1)  # run
            elif player.in_air:
                player.update_action(2)  # jump
            else:
                player.update_action(0)  # idle
            player.move(moving_left, moving_right)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    moving_left = True
                if event.key == pygame.K_RIGHT:
                    moving_right = True
                if event.key == pygame.K_UP and player.alive:
                    player.jump = True
                if event.key == pygame.K_SPACE:
                    shoot = True
                if event.key == pygame.K_ESCAPE:
                    running = False

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    moving_left = False
                if event.key == pygame.K_RIGHT:
                    moving_right = False
                if event.key == pygame.K_SPACE:
                    shoot = False

        pygame.display.update()
        clock.tick(60)
