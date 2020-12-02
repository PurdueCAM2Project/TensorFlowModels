import tensorflow as tf
from yolo.modeling.layers import nn_blocks

class YoloHead(tf.keras.layers.Layer):
    def __init__(self,
                 classes=80,
                 boxes_per_level=3,
                 output_extras=0,
                 xy_exponential=False,
                 exp_base=2,
                 xy_scale_base="default_value",
                 norm_momentum=0.99,
                 norm_epsilon=0.001,
                 kernel_initializer='glorot_uniform',
                 kernel_regularizer=None,
                 bias_regularizer=None,
                 **kwargs):
        
        self._classes = classes
        self._boxes_per_level = boxes_per_level
        self._output_extras = output_extras

        self._output_conv = (classes + output_extras + 5) * boxes_per_level

        self._masks = None
        self._path_scales = None
        self._x_y_scales = None
        self._xy_exponential = xy_exponential
        self._exp_base = exp_base
        self._xy_scale_base = xy_scale_base

        self._norm_momentum = norm_momentum
        self._norm_epsilon = norm_epsilon
        self._kernel_initializer = kernel_initializer
        self._kernel_regularizer = kernel_regularizer
        self._bias_regularizer = bias_regularizer

        self._base_config = dict(
                filters=self._output_conv,
                kernel_size=(1, 1),
                strides=(1, 1),
                padding="same",
                use_bn=False,
                activation=None,
                norm_momentum=self._norm_momentum,
                norm_epsilon=self._norm_epsilon,
                kernel_initializer=self._kernel_initializer,
                kernel_regularizer=self._kernel_regularizer,
                bias_regularizer=self._bias_regularizer)

        super(YoloHead, self).__init__(**kwargs)
        return 
    
    def build(self, inputs):
        self.key_list = inputs.keys()

        keys = [int(key) for key in self.key_list]
        self._min_level = min(keys)
        self._max_level = max(keys)

        self._head = dict()
        for key in self.key_list: 
            self._head[key] = nn_blocks.ConvBN(**self._base_config)
        self._get_filtering_attributes(xy_exponential=self._xy_exponential, exp_base=self._exp_base, xy_scale_base=self._xy_scale_base)
        return 
    
    def call(self, inputs):
        outputs = dict()
        for key in self.key_list:
            outputs[key] = self._head[key](inputs[key])
        return outputs

    def _get_filtering_attributes(self,
                                  xy_exponential=False,
                                  exp_base=2,
                                  xy_scale_base="default_value"):
        start = 0
        boxes = {}
        path_scales = {}
        scale_x_y = {}

        if xy_scale_base == "default_base":
            xy_scale_base = 0.05
            xy_scale_base = xy_scale_base / (
                self._boxes_per_level *
                (self._max_level - self._min_level + 1) - 1)
        elif xy_scale_base == "default_value":
            xy_scale_base = 0.00625

        for i in range(self._min_level, self._max_level + 1):
            boxes[str(i)] = list(range(start, self._boxes_per_level + start))
            path_scales[str(i)] = 2**i
            if xy_exponential:
                scale_x_y[str(i)] = 1.0 + xy_scale_base * (exp_base**i)
            else:
                scale_x_y[str(i)] = 1.0
            start += self._boxes_per_level
        
        self._masks = boxes
        self._path_scales = path_scales
        self._x_y_scales= scale_x_y
        return 

    @property
    def output_depth(self):
        return (self._classes + self._output_extras + 5) * self._boxes_per_level

    @property
    def masks(self):
        if self._masks == None: 
            raise Exception("model has to be built before the masks can be determined")
        return self._masks

    @property
    def path_scales(self):
        if self._path_scales == None: 
            raise Exception("model has to be built before the path_scales can be determined")
        return self._path_scales

    @property
    def scale_xy(self):
        if self._x_y_scales == None: 
            raise Exception("model has to be built before the x_y_scales can be determined")
        return self._x_y_scales
    
    @property
    def num_boxes(self):
        if self._min_level == None or self._max_level == None: 
            raise Exception("model has to be built before number of boxes can be determined")
        return (self._max_level - self._min_level + 1) * self._boxes_per_level