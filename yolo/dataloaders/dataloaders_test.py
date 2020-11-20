from .YOLO_Detection_Input import Parser
from .tfds_coco_decoder import MSCOCODecoder
import tensorflow_datasets as tfds
from matplotlib import pyplot as plt
from matplotlib import patches
from yolo.utils.box_utils import xcycwh_to_xyxy

dataset = tfds.load('coco/2017', split='train')

decoder = MSCOCODecoder()
parser = Parser()

dataset = dataset.map(decoder.decode)
imgs = dataset.map(parser._parse_train_data)
#imgs = dataset.map(parser._parse_eval_data)
for img, label in imgs.take(10):
    fig,ax = plt.subplots(1)
    # Display the image
    ax.imshow(img)
    # Create a Rectangle patch
    for bbox in label['bbox'].numpy():
        bbox = xcycwh_to_xyxy(bbox).numpy()
        wh = bbox[2:4] - bbox[0:2]
        print(bbox * 416, wh * 416)
        rect = patches.Rectangle(bbox[0:2] * 416,wh[0] * 416,wh[1] * 416,linewidth=1,edgecolor='r',facecolor='none')
        ax.add_patch(rect)
    # Add the patch to the Axes
    plt.show()
