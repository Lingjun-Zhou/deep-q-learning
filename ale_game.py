from ale_python_interface import ALEInterface
import numpy as np
from skimage import measure


def init(display_screen=False, record_dir=None):
    if display_screen:
        import pygame
        pygame.init()
    rom_path = '.'
    ale = ALEInterface()
    ale.setBool('display_screen', display_screen)
    ale.setInt('random_seed', 123)
    if record_dir is not None:
        ale.setString("record_screen_dir", record_dir)
    ale.loadROM(rom_path + '/space_invaders.bin')
    ale.setFloat("repeat_action_probability", 0)

    return ale


class Phi(object):
    def __init__(self, skip_every):
        self.prev_cropped = np.zeros((80, 80), dtype=np.uint8)
        self.prev_frames = [np.zeros((80, 80), dtype=np.uint8), np.zeros((80, 80), dtype=np.uint8), np.zeros((80, 80), dtype=np.uint8), np.zeros((80, 80), dtype=np.uint8)]
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
            return tuple(self.prev_frames)  # deepcopy would be slower
        else:
            self.prev_cropped = cropped
            return tuple(self.prev_frames)


class SpaceInvadersGameCombined2Visualizer:
    def __init__(self):
        import pygame
        self.screen = pygame.display.set_mode((160, 640))
        self.mem = {}

    def show(self, prev_frames):
        import pygame

        def l(x):
            if x not in self.mem:
                self.mem[x] = (x, x, x)
            return self.mem[x]

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

# 0 nothing
# 1 ^
# 2 ->
# 3 <-
# 4 -> and ^
# 5 <- and ^

    def __init__(self, ale):
        self.ale = ale
        self.finished = False
        self.cum_reward = 0
        self.state = np.mean(ale.getScreenRGB(), axis=2, dtype=np.uint8)
        self.action_set = self.ale.getMinimalActionSet()
        self.lives = 4

    def n_actions(self):
        return len(self.action_set)

    def input(self, action):
        self.cum_reward += self.ale.act(self.action_set[action])
        if self.ale.game_over():
            self.finished = True
            self.ale.reset_game()

        self.state = np.mean(self.ale.getScreenRGB(), axis=2, dtype=np.uint8)
        if self.lives != self.ale.lives():
            self.lives = self.ale.lives()
            return 40
        else:
            return 0

    def get_state(self):
        return self.state
