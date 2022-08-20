from numpy.lib.function_base import angle
import time
import numpy as np
import cv2
from Detect import Detect

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'
import sys
import pygame
import random

def play_dinosaur_game():
    # Init Webcam    
    wCam, hCam = 1280, 720
    cap = cv2.VideoCapture(0)
    cap.set(3, wCam)
    cap.set(4, hCam)
    print("Make sure the webcam can see your face")

    headY = 0
    headDir = ""

    detector = Detect()
    count = 0
    dir = 0

    # Initialize pygame
    pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=256)
    pygame.init()
    # https://stackoverflow.com/questions/36062177/when-do-i-need-to-use-mixer-pre-init-as-oppsed-to-just-mixer-init
    random.seed()
    
    # Game Variables
    floor_x_pos = 0
    cloud_list = []
    game_active = False
    crouching = False
    floor_speed = 0
    dinosaur_jump_speed = 0
    has_jumped = False
    obstical_surface_list = []
    obstical_rect_list = []
    obstical_index_list = []
    first_game = True
    first_jump = True
    screen_index = 80
    first_ground_hit = False
    shift = 38

    # Create window and fill white
    global screen
    screen = pygame.display.set_mode((1200, 300))
    pygame.display.set_caption("Exercise Dinosaur Game")

    # Create Clock
    clock = pygame.time.Clock()

    # script_dir is the file directory of the file
    script_dir = os.path.dirname(__file__)

    # Font
    score_font = pygame.font.Font(os.path.join(script_dir, './assets/font/PressStart2P-Regular.ttf'), 12)
    game_over_font = pygame.font.Font(os.path.join(script_dir, './assets/font/PressStart2P-Regular.ttf'), 15)

    # Load image function to keep code dry
    def load_image(name, scale):
        surface = pygame.image.load(os.path.join(script_dir, 'assets', 'images', name)).convert_alpha()
        surface = pygame.transform.rotozoom(surface, 0, scale)
        return surface

    # Floor
    floor_surface = load_image('floor.png', 0.5)

    # Cloud
    cloud_surface = load_image('cloud.png', 0.8)
    CLOUD = pygame.USEREVENT
    pygame.time.set_timer(CLOUD, 500)

    # Dinosaur
    walk_1 = load_image('walk1.png', 0.8)
    walk_2 = load_image('walk2.png', 0.8)
    duck_1 = load_image('duck1.png', 0.8)
    duck_2 = load_image('duck2.png', 0.8)
    death_image = load_image('death2.png', 0.8)
    stand_image = load_image('stand.png', 0.8)
    dinosaur_list = [walk_1, walk_2, duck_1, duck_2]
    walk_index = 0
    dinosaur_surface = dinosaur_list[walk_index]
    dinosaur_rect = dinosaur_surface.get_rect(midbottom = (80, 285))
    WALK = pygame.USEREVENT + 1
    pygame.time.set_timer(WALK, 100)

    # Cactus
    small_cactus_1 = load_image('small_cactus1.png', 0.8)
    small_cactus_2 = load_image('small_cactus2.png', 0.8)
    large_cactus_1 = load_image('large_cactus1.png', 0.8)
    bird_1 = load_image('bird1.png', 0.8)
    bird_2 = load_image('bird2.png', 0.8)
    obstical_type_list = [small_cactus_1, small_cactus_2, large_cactus_1, bird_1, bird_2]
    CACTUSSPAWN = pygame.USEREVENT + 2
    pygame.time.set_timer(CACTUSSPAWN, 1000)

    # Game Over button
    game_over_button = load_image('restart.png', 0.8)

    # Sounds
    jump_sound = pygame.mixer.Sound(os.path.join(script_dir, './assets/sounds/jump.wav'))
    death_sound = pygame.mixer.Sound(os.path.join(script_dir, './assets/sounds/death.wav'))
    point_sound = pygame.mixer.Sound(os.path.join(script_dir, './assets/sounds/point.wav'))

    # Score
    score = 0
    high_score = 0
    SCOREEVENT = pygame.USEREVENT + 10
    pygame.time.set_timer(SCOREEVENT, 100)

    # Open saved high score. If the file or directory does not exist, create them.
    try:
        os.makedirs("data")
    except FileExistsError:
        pass

    try:
        with open(os.path.join(script_dir, 'data', 'score.txt'), 'r') as f:
            high_score = int(f.readline())
    except FileNotFoundError:
        with open(os.path.join(script_dir, 'data', 'score.txt'), 'w') as f:
            f.write("0")
    
    while True:
        success, img = cap.read()
        img = detector.findPose(img, False)
        lmList = detector.findPosition(img, False)

        if len(lmList) != 0:
            # Left arm
            angleLeft = detector.findAngle(img, 23, 25, 27)
            # Right arm
            angleRight =  detector.findAngle(img, 24, 26, 28)
            
            perLeft = np.interp(angleLeft, (80, 140), (0, 100))
            # perRight = np.interp(angleRight, (80, 140), (0, 100))

            headYCurrent = detector.findDir(img, 0)[1]
            
            if(headY == 0):
                headY = headYCurrent
            else:
                if (headYCurrent > headY and headYCurrent - headY > 50):
                    headY = headYCurrent
                    headDir = "Down"

                elif (headYCurrent < headY and  headY - headYCurrent > 50):
                    headY = headYCurrent
                    headDir = "Up"


            # Check (count)
            if perLeft == 100:
                if dir == 0:
                    count += 0.5
                    dir = 1
            if perLeft == 0:
                if dir == 1:
                    if (headDir == "Down" and game_active):
                        count += 0.5
                        dir = 0
                        print("Down")
                        crouching = True

                    elif (headDir == "Up" and game_active):
                        print("Jump")
                        if not(has_jumped):
                            dinosaur_jump_speed = 12
                            jump_sound.play()
                            crouching = False
                        count += 0.5
                        dir = 0

                    elif headDir == "Up" and not(game_active) and not(first_game):
                        print("Jump")
                        dinosaur_rect = dinosaur_surface.get_rect(midbottom = (80, 285))
                        if score > high_score:
                            high_score = score
                        obstical_index_list.clear()
                        obstical_rect_list.clear()
                        obstical_surface_list.clear()
                        floor_speed = 4
                        dinosaur_jump_speed = 0
                        score = 0
                        crouching = False
                        jump_sound.play()
                        game_active = True
                        count += 0.5
                        dir = 0

                    elif headDir == "Up" and not(game_active) and first_game:
                        print("Jump")
                        dinosaur_jump_speed = 12
                        jump_sound.play()
                        crouching = False
                        count += 0.5
                        dir = 0


            # Count
            cv2.rectangle(img, (25, 125), (125, 25), (0, 255, 0), cv2.FILLED)
            cv2.putText(img, str(int(count-0.5)), (50, 100),
                        cv2.FONT_HERSHEY_COMPLEX, 2, (255, 0, 0), 2)

        
        # Event loop
        for event in pygame.event.get():

            # Quit if window is closed
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)

            # Spawn Cloud
            if event.type == CLOUD and game_active:
                if random.randint(1, 10) == 1:
                    cloud_list.append(create_cloud(cloud_surface))

            # Walk animation
            if event.type == WALK and not(crouching) and game_active:
                if walk_index != 0:
                    walk_index = 0
                else:
                    walk_index = 1
                dinosaur_surface, dinosaur_rect = dino_animation(walk_index, dinosaur_list, dinosaur_rect)
            elif event.type == WALK and crouching and game_active:
                if walk_index != 2:
                    walk_index = 2
                else:
                    walk_index = 3
                dinosaur_surface, dinosaur_rect = dino_animation(walk_index, dinosaur_list, dinosaur_rect)
            
            # Spawn Cactus
            if event.type == CACTUSSPAWN and game_active:
                if random.randint(1,1000) > 900:
                    temp_surface, temp_rect, temp_index = spawn_cactus(obstical_type_list, score)
                    obstical_surface_list.append(temp_surface)
                    obstical_rect_list.append(temp_rect)
                    obstical_index_list.append(temp_index)

                # Remove Cactus
                obstical_surface_list, obstical_rect_list, obstical_index_list = remove_cactus(obstical_surface_list, obstical_rect_list, obstical_index_list)

            # Score
            if event.type == SCOREEVENT and game_active:
                score += 1
                if score % 500 == 0:
                    point_sound.play()
                    floor_speed += 1
                if score % 150 == 0 and score < 900:
                    pygame.time.set_timer(CACTUSSPAWN, 1000 - score // 3)

        screen.fill((255, 255, 255))

        # Clouds
        if game_active:
            cloud_list = move_clouds(cloud_list)
        draw_clouds(cloud_list, cloud_surface, screen)

        # Floor
        floor_x_pos -= floor_speed
        draw_floor(floor_x_pos, floor_surface)
        if floor_x_pos <= -1200:
            floor_x_pos = 0

        # Cactus
        obstical_rect_list = move_cactus(obstical_rect_list, floor_speed)
        draw_cactus(obstical_surface_list, obstical_rect_list, obstical_index_list)
        if game_active:
            obstical_surface_list, obstical_index_list = animate_bird(obstical_index_list, obstical_surface_list, obstical_type_list)
        
        # Dinosaur
        dinosaur_rect.bottom -= dinosaur_jump_speed
        if dino_on_ground(dinosaur_rect):
            has_jumped = False
            dinosaur_rect.bottom = 285
            dinosaur_jump_speed = 0
        else:
            has_jumped = True
            if game_active or first_game:
                dinosaur_jump_speed -= 0.3
                if first_game and dinosaur_rect.bottom < 210:
                    first_jump = False
            else:
                dinosaur_jump_speed = 0
        if game_active == False:
            dinosaur_surface = death_image
            dinosaur_rect = dinosaur_surface.get_rect(midbottom = (83, dinosaur_rect.bottom))
        if not(first_game):
            screen.blit(dinosaur_surface, dinosaur_rect)

        # Collision detection and changes
        if check_collision(dinosaur_rect, obstical_rect_list):
            floor_speed = 0
            if game_active:
                death_sound.play()
            game_active = False

            # If there is a new high score, save it to score.txt
            temp_high_score = max(high_score, score)
            with open(os.path.join(script_dir, 'data', 'score.txt'), 'w') as f:
                f.write(str(temp_high_score))
            
        if game_active == False:
             game_over_display(screen, game_over_font, game_over_button, first_game)   

        # Score
        display_score(score, high_score, score_font, screen)

        # First Game
        if first_game and not(game_active):
            if first_ground_hit == False:
                dinosaur_surface = stand_image
                dinosaur_rect = dinosaur_surface.get_rect(midbottom = (38, dinosaur_rect.bottom))
                screen.blit(dinosaur_surface, dinosaur_rect)
            if first_jump:
                pygame.draw.rect(screen, (255, 255, 255), (screen_index, 0, 1220, 300))
            else:
                screen_index += 5
                pygame.draw.rect(screen, (255, 255, 255), (screen_index, 0, 1220, 300))
                if dino_on_ground(dinosaur_rect) or first_ground_hit:
                    first_ground_hit = True
                    floor_speed = 4
                    if walk_index != 0:
                        walk_index = 0
                    else:
                        walk_index = 1
                    dinosaur_surface = dinosaur_list[walk_index]
                    dinosaur_rect = dinosaur_surface.get_rect(midbottom = (shift, dinosaur_rect.bottom))
                    if shift < 83:
                        shift += 1
                    if screen_index == 1200:
                        first_game = False
                        game_active = True
                    screen.blit(dinosaur_surface, dinosaur_rect)
        pygame.display.update()
        clock.tick(120)


        cv2.imshow("Image", img)
        # key = cv2.waitKey(1)
        # if key == ord("q"):
        #     break

def draw_floor(floor_x_pos, floor_surface):
    screen.blit(floor_surface, (floor_x_pos, 275))
    screen.blit(floor_surface, (floor_x_pos + 1200, 275))

def create_cloud(cloud_surface):
    cloud_rect = cloud_surface.get_rect(center = (1300, random.randint(50, 125)))
    return cloud_rect

def move_clouds(clouds):
    for cloud in clouds:
        cloud.centerx -= 1

        if cloud.right <= -10:
            clouds.remove(cloud)

    return clouds

def draw_clouds(clouds, cloud_surface, screen):
    for cloud in clouds:
        screen.blit(cloud_surface, cloud)

def display_score(score, high_score, game_font, screen):
    if score < 100 or score % 100 > 25:
        score_surface = game_font.render('{:05d}'.format(score), True, (83, 83, 83))
    elif score % 100 <= 5:
        score_surface = game_font.render('     ', True, (83, 83, 83))
    elif score % 100 <= 10:
        score_surface = game_font.render('{:05d}'.format(score // 100 * 100), True, (83, 83, 83))
    elif score % 100 <= 15:
        score_surface = game_font.render('     ', True, (83, 83, 83))
    elif score % 100 <= 20:
        score_surface = game_font.render('{:05d}'.format(score // 100 * 100), True, (83, 83, 83))
    elif score % 100 <= 25:
        score_surface = game_font.render('     ', True, (83, 83, 83))
    
    score_rect = score_surface.get_rect(midright = (1190, 20))
    screen.blit(score_surface, score_rect)

    high_score_surface = game_font.render('HI {:05d}'.format(high_score), True, (117, 117, 117))
    high_score_rect = high_score_surface.get_rect(midright = (1120, 20))
    screen.blit(high_score_surface, high_score_rect)

def dino_animation(dino_index, dinosaur_list, dinosaur_rect):
    dino = dinosaur_list[dino_index]
    dino_rect = dino.get_rect(midbottom = (dinosaur_rect.centerx, dinosaur_rect.bottom))
    return dino, dino_rect

def dino_on_ground(dinosaur_rect):
    if dinosaur_rect.bottom >= 285:
        return True
    else:
        return False

def spawn_cactus(obstical_type_list, score):
    heights = [205, 235, 285]
    rand = 0
    if score <= 500:
        index = random.randint(0,2)
    # elif 500 < score <= 1000:
    #     index = random.randint(0,3)
    #     rand = random.randint(-10, 10)
    else:
        index = random.randint(0,4)
        rand = random.randint(-25, 25)
    cactus_surface = obstical_type_list[index]
    if index < 3:
        cactus_rect = cactus_surface.get_rect(midbottom = (1300 + rand, 290))
    else:
        cactus_rect = cactus_surface.get_rect(midbottom = (1300, random.choice(heights)))
    return cactus_surface, cactus_rect, index

def move_cactus(obstical_rect_list, floor_speed):
    for cactus in obstical_rect_list:
        cactus.centerx -= floor_speed
    return obstical_rect_list

def draw_cactus(obstical_surface_list, obstical_rect_list, obstical_index_list):
    for x in range(len(obstical_rect_list)):
        screen.blit(obstical_surface_list[x], obstical_rect_list[x])

def remove_cactus(obstical_surface_list, obstical_rect_list, obstical_index_list):
    
    for rect in obstical_rect_list:
        if rect.centerx <= -100:
            del obstical_surface_list[0:1]
            del obstical_rect_list[0:1]
            del obstical_index_list[0:1]
    return obstical_surface_list, obstical_rect_list, obstical_index_list

def animate_bird(obstical_index_list, obstical_surface_list, obstical_type_list):
    for x in range(len(obstical_index_list)):
        if obstical_index_list[x] == 6:
            obstical_surface_list[x] = obstical_type_list[6]
            obstical_index_list[x] = 7
        elif obstical_index_list[x] == 7:
            obstical_surface_list[x] = obstical_type_list[7]
            obstical_index_list[x] = 6
    return obstical_surface_list, obstical_index_list

def check_collision(single_rect, rect_list):
    for rect in rect_list:
        if single_rect.colliderect(rect):
            return True
    return False

def game_over_display(screen, game_over_font, game_over_button, first_game):
    if not(first_game):
        game_over_surface = game_over_font.render('G A M E   O V E R', True, (83, 83, 83))
        game_over_rect = game_over_surface.get_rect(midtop = (600, 80))
        screen.blit(game_over_surface, game_over_rect)

        button_rect = game_over_button.get_rect(center = (600, 150))
        screen.blit(game_over_button, button_rect)
