from ale_python_interface import ALEInterface
import numpy as np
import pygame
from skimage import measure
from copy import deepcopy
import scipy
from scipy import signal

# Set USE_SDL to true to display the screen. ALE must be compilied
# with SDL enabled for this to work. On OSX, pygame init is used to
# proxy-call SDL_main.

# USE_SDL = False
# if USE_SDL:
#  if sys.platform == 'darwin':   
#    import pygame
#    pygame.init() 
#    ale.setBool('sound', False) # Sound doesn't work on OSX    
#  elif sys.platform.startswith('linux'):
#    ale.setBool('sound', True)


# ale.setString("record_screen_dir", "record")

# Load the ROM file
# ale.setBool('display_screen', True)

ARR = {0: (0, 0, 0),
       6: (200, 200, 0),
       20: (0, 200, 200),
       52: (200, 0, 200),
       82: (0, 0, 200),
       196: (196, 0, 0),
       226: (0, 226, 0),
       246: (146, 0, 0)}
COLORS = sorted(ARR.keys())

gray_scale_lookup = {0: (0, 0, 0),
                     6: (30, 30, 30),
                     20: (60, 60, 60),
                     52: (90, 90, 90),
                     82: (120, 120, 120),
                     196: (150, 150, 150),
                     226: (180, 180, 180),
                     246: (210, 210, 210)}

mergeArr = {0: 0,
            6: 6,
            20: 20,  # robaki
            52: 52,  # oslony
            196: 196,
            226: 0,
            246: 0}

mergeArrValuesSet = set(mergeArr.values())
mergeArrValues = sorted(list(mergeArrValuesSet))


def init():
    pygame.init()
    rom_path = '/Users/maciej/Development/atari-roms'
    ale = ALEInterface()
    ale.setInt('random_seed', 123)
    ale.setBool('frame_skip', 1)
    ale.loadROM(rom_path + '/space_invaders.bin')
    ale.setFloat("repeat_action_probability", 0)
    return ale


def vectorize_single_group(vec):
    return map(lambda e: e in vec, mergeArrValues)


def vectorized(scr, desired_width, desired_height):
    grouped = \
        np.reshape(
            np.swapaxes(np.reshape(scr, (desired_width, 210 / desired_width, desired_height, 160 / desired_height)), 1,
                        2), (desired_width, desired_height, 160 * 210 / desired_width / desired_height))
    return np.apply_along_axis(vectorize_single_group, axis=2, arr=grouped)


class SpaceInvadersGameVectorizedVisualizer:
    def __init__(self):
        self.desired_width = 14
        self.desired_height = 20
        self.screen = pygame.display.set_mode((self.desired_height * 16, self.desired_width * 16))

    def show_vectorized(self, vec):
        rect = pygame.Surface((2, 14))
        border = pygame.Surface((16, 16))

        border.fill((255, 255, 255))
        for y in range(0, self.desired_width):
            for x in range(0, self.desired_height):
                # border_rect = pygame.Rect(x, y, 16, 16)
                # self.screen.blit(border, (x*16, y*16))

                for i_color in range(len(mergeArrValues)):
                    if vec[y][x][i_color]:
                        rect.fill(ARR[COLORS[i_color]])
                    else:
                        rect.fill((0, 0, 0))
                    self.screen.blit(rect, (x * 16 + 1 + i_color * 2, y * 16 + 1))

        pygame.display.flip()

    def show(self, game):
        self.show_vectorized(vectorized(game.get_state(), self.desired_width, self.desired_height))

    def next_game(self):
        pass


class SpaceInvadersGameVisualizer:
    def __init__(self):
        self.desired_width = 160
        self.desired_height = 210
        self.screen = pygame.display.set_mode((160, 210))

    def show(self, game):
        l = lambda x: ARR[x]
        rect = pygame.Surface((160, 210))

        arr_to_blit = np.reshape(zip(*list(np.frompyfunc(l, 1, 3)(game.get_state()))), (210, 160, 3))
        pygame.surfarray.blit_array(rect, np.transpose(arr_to_blit, [1, 0, 2]))
        self.screen.blit(rect, (0, 0))

        pygame.display.flip()

    def next_game(self):
        pass


class SpaceInvadersGameCombinedVisualizer:
    def __init__(self):
        self.screen = pygame.display.set_mode((80, 320))
        self.prev_cropped = np.zeros((80, 80))
        self.prev_frames = [np.zeros((80, 80)), np.zeros((80, 80)), np.zeros((80, 80)), np.zeros((80, 80))]

    def show(self, game):
        l = lambda x: gray_scale_lookup[x]
        f_l = np.frompyfunc(l, 1, 3)
        rect = pygame.Surface((80, 320))

        from skimage import measure
        cropped = measure.block_reduce((np.reshape(game.get_state(), (210, 160))[35:-15, :]), (2, 2), func=np.max)
        frame = np.maximum(cropped, self.prev_cropped)
        self.prev_cropped = cropped

        self.prev_frames.append(frame)
        self.prev_frames = self.prev_frames[1:]

        image = np.reshape(zip(*list(f_l(np.concatenate(self.prev_frames).flatten()))), (320, 80, 3))

        image = np.transpose(image, [1, 0, 2])
        print(np.shape(image))
        pygame.surfarray.blit_array(rect, image)
        self.screen.blit(rect, (0, 0))

        pygame.display.flip()

    def next_game(self):
        pass


class Phi(object):
    def __init__(self, skip_every):
        self.prev_cropped = np.zeros((80, 80))
        self.prev_frames = [np.zeros((80, 80)), np.zeros((80, 80)), np.zeros((80, 80)), np.zeros((80, 80))]
        self.frame_count = -1
        self.skip_every = skip_every

    def __call__(self, state):
        self.frame_count += 1

        cropped = measure.block_reduce((np.reshape(state, (210, 160))[35:-15, :]), (2, 2), func=np.max)

        if self.frame_count % self.skip_every == self.skip_every - 1:
            frame = np.maximum(cropped, self.prev_cropped)
            self.prev_frames.append(frame)
            self.prev_frames = self.prev_frames[1:]
            self.prev_cropped = cropped
            return tuple(self.prev_frames) # deepcopy would be slower
        else:
            self.prev_cropped = cropped
            return tuple(self.prev_frames)


class SpaceInvadersGameCombined2Visualizer:
    def __init__(self):
        self.screen = pygame.display.set_mode((160, 640))

    def show(self, prev_frames):
        l = lambda x: gray_scale_lookup[x]
        f_l = np.frompyfunc(l, 1, 3)
        rect = pygame.Surface((160, 640))

        image = np.reshape(zip(*list(f_l(np.concatenate(prev_frames).flatten()))), (320, 80, 3))

        image = np.transpose(image, [1, 0, 2])

        pygame.surfarray.blit_array(rect, np.repeat(np.repeat(image, 2, axis=0), 2, axis=1))
        self.screen.blit(rect, (0, 0))

        pygame.display.flip()

    def next_game(self):
        pass


class SpaceInvadersGame(object):
    def __init__(self, ale):
        self.ale = ale
        self.finished = False
        self.cum_reward = 0
        self.state = ale.getScreen()
        self.action_set = self.ale.getMinimalActionSet()

    def n_actions(self):
        return len(self.action_set)

    def input(self, action):
        # print ("action: ", action)
        self.cum_reward += self.ale.act(self.action_set[action])
        if self.ale.game_over():
            print ("finished!")
            self.finished = True
            self.ale.reset_game()

        self.state = self.ale.getScreen()
        return self

    def get_state(self):
        return self.state
