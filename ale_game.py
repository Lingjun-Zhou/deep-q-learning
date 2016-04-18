from __future__ import division
from ale_python_interface import ALEInterface
import numpy as np
from skimage import measure
import skimage.transform

def init(game, display_screen=False, record_dir=None):
    if display_screen:
        import pygame
        pygame.init()
    ale = ALEInterface()
    ale.setBool('display_screen', display_screen)
    ale.setInt('random_seed', 123)
    if record_dir is not None:
        ale.setString("record_screen_dir", record_dir)
    ale.loadROM('{game}.bin'.format(game=game))
    ale.setFloat("repeat_action_probability", 0)

    return ale


class Phi3(object):

    def __init__(self):
        self.screen_size = 84

    def __call__(self, frames):
        last = frames[3:16:4]
        sec_last = frames[2:16:4]
        return [self.resize_and_crop(img) for img in np.max([last, sec_last], axis=0)]

    @staticmethod
    def resize_and_crop(im):
        # Resize so smallest dim = 256, preserving aspect ratio
        im = im[40:-10, :]
        h, w = im.shape
        if h < w:
            im = skimage.transform.resize(im, (84, w*84//h), preserve_range=True)
        else:
            im = skimage.transform.resize(im, (h*84//w, 84), preserve_range=True)

        # Central crop to 224x224
        h, w = im.shape
        return im[h//2-42:h//2+42, w//2-42:w//2+42].astype(dtype=np.uint8)


class Phi2(object):

    def __init__(self, skip_every, reshape):
        self.screen_size = 84
        self.prev_cropped = np.zeros((self.screen_size, self.screen_size), dtype=np.uint8)
        self.prev_frames = [np.zeros((self.screen_size, self.screen_size), dtype=np.uint8),
                            np.zeros((self.screen_size, self.screen_size), dtype=np.uint8),
                            np.zeros((self.screen_size, self.screen_size), dtype=np.uint8),
                            np.zeros((self.screen_size, self.screen_size), dtype=np.uint8)]
        self.frame_count = -1
        self.skip_every = skip_every
        self.reshape = reshape
        if reshape != "mean":
            raise RuntimeError("Unknown reshape method: {reshape} for Phi2".format(reshape=self.reshape))

    def __call__(self, state):
        self.frame_count += 1
        cropped = self.resize_and_crop(state)

        if self.frame_count % self.skip_every == self.skip_every - 1:
            frame = np.maximum(cropped, self.prev_cropped)
            self.prev_frames.append(frame)
            self.prev_frames = self.prev_frames[1:]
            self.prev_cropped = cropped
            return tuple(self.prev_frames)  # deepcopy would be slower
        else:
            self.prev_cropped = cropped
            return tuple(self.prev_frames)

    @staticmethod
    def resize_and_crop(im):
        # Resize so smallest dim = 256, preserving aspect ratio
        im = im[40:-10, :]
        h, w = im.shape
        if h < w:
            im = skimage.transform.resize(im, (84, w*84//h), preserve_range=True)
        else:
            im = skimage.transform.resize(im, (h*84//w, 84), preserve_range=True)

        # Central crop to 224x224
        h, w = im.shape
        return im[h//2-42:h//2+42, w//2-42:w//2+42].astype(dtype=np.uint8)


class Phi(object):
    def __init__(self, skip_every, reshape):
        self.screen_size = 80
        self.prev_cropped = np.zeros((self.screen_size, self.screen_size), dtype=np.uint8)
        self.prev_frames = [np.zeros((self.screen_size, self.screen_size), dtype=np.uint8),
                            np.zeros((self.screen_size, self.screen_size), dtype=np.uint8),
                            np.zeros((self.screen_size, self.screen_size), dtype=np.uint8),
                            np.zeros((self.screen_size, self.screen_size), dtype=np.uint8)]
        self.frame_count = -1
        self.skip_every = skip_every
        self.reshape = reshape

    def __call__(self, state):
        self.frame_count += 1
        if self.reshape == "max":
            cropped = measure.block_reduce((np.reshape(state, (210, 160))[35:-15, :]), (2, 2), func=np.max)
        elif self.reshape == "mean":
            cropped = measure.block_reduce((np.reshape(state, (210, 160))[40:-10, :]), (2, 2), func=np.mean).astype(dtype=np.int8)
        else:
            raise RuntimeError("Unknown reshape method: {reshape}".format(reshape=self.reshape))

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
    def __init__(self, screen_size):
        import pygame
        self.screen_size = screen_size
        self.screen = pygame.display.set_mode((screen_size * 2, screen_size * 8))
        self.mem = {}

    def show(self, prev_frames):
        import pygame

        def l(x):
            if x not in self.mem:
                self.mem[x] = (x, x, x)
            return self.mem[x]

        f_l = np.frompyfunc(l, 1, 3)
        rect = pygame.Surface((self.screen_size * 2, self.screen_size * 8))
        image = np.reshape(zip(*list(f_l(np.concatenate(prev_frames).flatten()))), (self.screen_size * 4, self.screen_size, 3))

        image = np.transpose(image, [1, 0, 2])
        pygame.surfarray.blit_array(rect, np.repeat(np.repeat(image, 2, axis=0), 2, axis=1))
        self.screen.blit(rect, (0, 0))

        pygame.display.flip()

    def next_game(self):
        pass


class ALEGame(object):

    def __init__(self, ale):
        self.ale = ale
        self.finished = False
        self.cum_reward = 0
        self.action_set = self.ale.getMinimalActionSet()

        self.h = 210
        self.w = 160

        self.prev_frames = [np.zeros((self.h, self.w), dtype=np.uint8),
                            np.zeros((self.h, self.w), dtype=np.uint8),
                            np.zeros((self.h, self.w), dtype=np.uint8),
                            np.zeros((self.h, self.w), dtype=np.uint8),

                            np.zeros((self.h, self.w), dtype=np.uint8),
                            np.zeros((self.h, self.w), dtype=np.uint8),
                            np.zeros((self.h, self.w), dtype=np.uint8),
                            np.zeros((self.h, self.w), dtype=np.uint8),

                            np.zeros((self.h, self.w), dtype=np.uint8),
                            np.zeros((self.h, self.w), dtype=np.uint8),
                            np.zeros((self.h, self.w), dtype=np.uint8),
                            np.zeros((self.h, self.w), dtype=np.uint8),

                            np.zeros((self.h, self.w), dtype=np.uint8),
                            np.zeros((self.h, self.w), dtype=np.uint8),
                            np.zeros((self.h, self.w), dtype=np.uint8),
                            np.zeros((self.h, self.w), dtype=np.uint8), ]

    def n_actions(self):
        return len(self.action_set)

    def input(self, action):
        lives_before = self.ale.lives()
        action_reward = self.ale.act(self.action_set[action])
        self.cum_reward += action_reward

        if self.ale.game_over():
            self.finished = True
            self.ale.reset_game()

        self.prev_frames.append(np.dot(self.ale.getScreenRGB(), np.array([0.2126, 0.7152, 0.0722])).astype(np.int8))
        self.prev_frames = self.prev_frames[1:]

        return action_reward, lives_before != self.ale.lives()

    def get_state(self):
        return self.prev_frames
