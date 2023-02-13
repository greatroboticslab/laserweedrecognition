import mmcv
from mmcls.datasets import build_dataset
from mmcls.core.evaluation import calculate_confusion_matrix
cfg = mmcv.Config.fromfile("../configs/resnet/resnet50_b32x8_imagenet.py")
dataset = build_dataset(cfg.data.test)
result = mmcv.load("../2022_det2cls_result.pkl")
matrix = calculate_confusion_matrix(result['class_scores'], dataset.get_gt_labels())
print(matrix)
import matplotlib.pyplot as plt
plt.imshow(matrix)   # Visualize the first twenty classes.
plt.show()