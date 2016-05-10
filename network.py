from __future__ import print_function
from __future__ import division

import lasagne


def build_nature_with_pad(n_actions, input_var, n_stack_frames, screen_size):
    network = lasagne.layers.InputLayer(shape=(None, n_stack_frames, screen_size[0], screen_size[1]),
                                        input_var=input_var)

    network = lasagne.layers.Conv2DLayer(
        network, num_filters=32, filter_size=(8, 8), stride=4, pad=2,
        nonlinearity=lasagne.nonlinearities.rectify,
        W=lasagne.init.GlorotUniform(),
        b=lasagne.init.Constant(.1))

    print(network.output_shape)

    network = lasagne.layers.Conv2DLayer(
        network, num_filters=64, filter_size=(4, 4), stride=2,
        nonlinearity=lasagne.nonlinearities.rectify,
        b=lasagne.init.Constant(.1))

    network = lasagne.layers.Conv2DLayer(
        network, num_filters=64, filter_size=(3, 3), stride=1,
        nonlinearity=lasagne.nonlinearities.rectify,
        b=lasagne.init.Constant(.1))

    network = lasagne.layers.DenseLayer(
        network,
        num_units=512,
        nonlinearity=lasagne.nonlinearities.rectify,
        b=lasagne.init.Constant(.1))

    network = lasagne.layers.DenseLayer(
        network,
        num_units=n_actions,
        nonlinearity=None,
        b=lasagne.init.Constant(.1))

    return network


def build_nature_with_pad_he(n_actions, input_var, n_stack_frames, screen_size):
    network = lasagne.layers.InputLayer(shape=(None, n_stack_frames, screen_size[0], screen_size[1]),
                                        input_var=input_var)

    network = lasagne.layers.Conv2DLayer(
        network, num_filters=32, filter_size=(8, 8), stride=4, pad=2,
        nonlinearity=lasagne.nonlinearities.rectify,
        W=lasagne.init.HeNormal(gain='relu'),
        b=lasagne.init.Constant(.1))

    print(network.output_shape)

    network = lasagne.layers.Conv2DLayer(
        network, num_filters=64, filter_size=(4, 4), stride=2,
        nonlinearity=lasagne.nonlinearities.rectify,
        W=lasagne.init.HeNormal(gain='relu'),
        b=lasagne.init.Constant(.1))

    network = lasagne.layers.Conv2DLayer(
        network, num_filters=64, filter_size=(3, 3), stride=1,
        nonlinearity=lasagne.nonlinearities.rectify,
        W=lasagne.init.HeNormal(gain='relu'),
        b=lasagne.init.Constant(.1))

    network = lasagne.layers.DenseLayer(
        network,
        num_units=512,
        nonlinearity=lasagne.nonlinearities.rectify,
        W=lasagne.init.HeNormal(gain='relu'),
        b=lasagne.init.Constant(.1))

    network = lasagne.layers.DenseLayer(
        network,
        num_units=n_actions,
        nonlinearity=None,
        b=lasagne.init.Constant(.1))

    return network


def build_nature(n_actions, input_var, n_stack_frames, screen_size, n_additional_params=0, additional_input_var=None):
    network = lasagne.layers.InputLayer(shape=(None, n_stack_frames, screen_size[0], screen_size[1]),
                                        input_var=input_var)

    if n_additional_params > 0:
        additional_params_layer = lasagne.layers.InputLayer(shape=(None, n_additional_params),
                                                            input_var=additional_input_var)

    network = lasagne.layers.Conv2DLayer(
        network, num_filters=32, filter_size=(8, 8), stride=4,
        nonlinearity=lasagne.nonlinearities.rectify,
        W=lasagne.init.GlorotUniform(),
        b=lasagne.init.Constant(.1))

    network = lasagne.layers.Conv2DLayer(
        network, num_filters=64, filter_size=(4, 4), stride=2,
        nonlinearity=lasagne.nonlinearities.rectify,
        b=lasagne.init.Constant(.1))

    network = lasagne.layers.Conv2DLayer(
        network, num_filters=64, filter_size=(3, 3), stride=1,
        nonlinearity=lasagne.nonlinearities.rectify,
        b=lasagne.init.Constant(.1))

    if n_additional_params > 0:
        print("Shape before concatenating {shape}".format(shape=network.output_shape))
        flattened = lasagne.layers.FlattenLayer(network)
        print("Shape flattened {shape}".format(shape=flattened.output_shape))
        print("Shape additional params {shape}".format(shape=additional_params_layer.output_shape))
        network = lasagne.layers.ConcatLayer([flattened, additional_params_layer])

        print("Shape after concatenating {shape}".format(shape=network.output_shape))

    network = lasagne.layers.DenseLayer(
        network,
        num_units=512,
        nonlinearity=lasagne.nonlinearities.rectify,
        b=lasagne.init.Constant(.1))

    network = lasagne.layers.DenseLayer(
        network,
        num_units=n_actions,
        nonlinearity=None,
        b=lasagne.init.Constant(.1))

    return network


def build_nips(n_actions, input_var, n_stack_frames, screen_size):
    network = lasagne.layers.InputLayer(shape=(32, n_stack_frames, screen_size[0], screen_size[1]),
                                        input_var=input_var)

    network = lasagne.layers.Conv2DLayer(
        network, num_filters=16, filter_size=(8, 8), stride=4,
        nonlinearity=lasagne.nonlinearities.rectify,
        W=lasagne.init.GlorotUniform())

    network = lasagne.layers.Conv2DLayer(
        network, num_filters=32, filter_size=(4, 4), stride=2,
        nonlinearity=lasagne.nonlinearities.rectify)

    network = lasagne.layers.DenseLayer(
        network,
        num_units=256,
        nonlinearity=lasagne.nonlinearities.rectify)

    network = lasagne.layers.DenseLayer(
        network,
        num_units=n_actions,
        nonlinearity=None,
        W=lasagne.init.HeUniform(),
        b=lasagne.init.Constant(.1))

    return network


def build_simple_breakout_W_caffe_normal(n_actions, input_var, n_stack_frames, screen_size):

    network = lasagne.layers.InputLayer(shape=(None, n_stack_frames, screen_size[0], screen_size[1]),
                                        input_var=input_var)

    network = lasagne.layers.Conv2DLayer(
        network, num_filters=4, filter_size=(3, 3), stride=1, pad=1,
        nonlinearity=lasagne.nonlinearities.rectify,
        W=lasagne.init.HeNormal(gain='relu'))

    network = lasagne.layers.DenseLayer(
        network,
        num_units=128,
        nonlinearity=lasagne.nonlinearities.rectify,
        W=lasagne.init.HeNormal(gain='relu'))

    network = lasagne.layers.DenseLayer(
        network,
        num_units=n_actions,
        nonlinearity=None,
        b=lasagne.init.Constant(.1))

    return network
