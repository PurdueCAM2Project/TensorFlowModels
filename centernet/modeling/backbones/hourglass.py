import tensorflow as tf

from centernet.configs import backbones as cfg
from centernet.modeling.layers import nn_blocks

# from official.vision.beta.modeling.backbones import factory
from official.vision.beta.modeling.layers import nn_blocks as official_nn_blocks
from utils import register

from typing import List


class Hourglass(tf.keras.Model):
  """
  CenterNet Hourglass backbone
  """

  def __init__(
      self,
      input_channel_dims: int,
      channel_dims_per_stage: List[int],
      blocks_per_stage: List[int],
      num_hourglasses: int,
      initial_downsample: bool = True,
      input_specs=tf.keras.layers.InputSpec(shape=[None, None, None, 3]),
      **kwargs):
    """
    Args:
        channel_dims_per_stage: list of filter sizes for Residual blocks
        blocks_per_stage: list of residual block repetitions per down/upsample
        num_hourglasses: integer, number of hourglass modules in backbone
        pre_layers: tf.keras layer to process input before stacked hourglasses
    """
    # yapf: disable
    input = tf.keras.layers.Input(shape=input_specs.shape[1:])
    x_inter = input

    # Create some intermediate and postlayers to generate the heatmaps
    # (document and make cleaner later)
    inp_filters = channel_dims_per_stage[0]

    # Create prelayers if downsampling input
    if initial_downsample:
      prelayer_kernel_size = 7
      prelayer_strides = 2
    else:
      prelayer_kernel_size = 3
      prelayer_strides = 1

    x_inter = tf.keras.layers.Conv2D(
        filters=input_channel_dims,
        kernel_size=prelayer_kernel_size,
        strides=prelayer_strides,
        padding='same', # TODO: Google used valid
        use_bias=True,
        activation='relu'
    )(x_inter)
    x_inter = official_nn_blocks.ResidualBlock(
        filters=inp_filters, use_projection=True, strides=prelayer_strides
    )(x_inter)

    all_heatmaps = []

    for i in range(num_hourglasses):
      # Create hourglass stacks
      x_hg = nn_blocks.HourglassBlock(
          channel_dims_per_stage=channel_dims_per_stage,
          blocks_per_stage=blocks_per_stage
      )(x_inter)

      # cnvs
      x_hg = tf.keras.layers.Conv2D(
          filters=inp_filters,
          kernel_size=(3, 3),
          strides=(1, 1),
          padding='same',
          use_bias=True,
          activation='relu'
      )(x_hg)

      all_heatmaps.append(x_hg)

      # between hourglasses, we insert intermediate layers
      if i < num_hourglasses - 1:
        # cnvs_
        inter_hg_conv1 = tf.keras.layers.Conv2D(
            filters=inp_filters, # TODO: input_channel_dims * 2 was here before
            kernel_size=(1, 1),
            strides=(1, 1),
            padding='same',
            use_bias=True,
            activation='linear'
        )(x_inter)

        # inters_
        inter_hg_conv2 = tf.keras.layers.Conv2D(
            filters=inp_filters,
            kernel_size=(1, 1),
            strides=(1, 1),
            padding='same',
            use_bias=True,
            activation='linear'
        )(x_hg)

        x_inter = inter_hg_conv1 + inter_hg_conv2
        x_inter = tf.keras.layers.ReLU()(x_inter)

        # inters
        x_inter = official_nn_blocks.ResidualBlock(
            filters=inp_filters, use_projection=True, strides=1 # TODO: strides=2 ?
        )(x_inter)
    # yapf: enable

    super().__init__(inputs=input, outputs=all_heatmaps, **kwargs)


# @factory.register_backbone_builder('hourglass')


@register.backbone('hourglass', cfg.Hourglass)
def build_hourglass(
    input_specs: tf.keras.layers.InputSpec,
    model_config,
    l2_regularizer: tf.keras.regularizers.Regularizer = None) -> tf.keras.Model:
  """Builds ResNet backbone from a config."""
  backbone_type = model_config.backbone.type
  backbone_cfg = model_config.backbone.get()
  assert backbone_type == 'hourglass', (f'Inconsistent backbone type '
                                        f'{backbone_type}')

  return Hourglass(
      input_channel_dims=backbone_cfg.input_channel_dims,
      channel_dims_per_stage=backbone_cfg.channel_dims_per_stage,
      blocks_per_stage=backbone_cfg.blocks_per_stage,
      num_hourglasses=backbone_cfg.num_hourglasses,
      initial_downsample=backbone_cfg.initial_downsample,
      input_specs=input_specs)
