#_base_ = 'resnet50_8xb32_in1k.py'
_base_ = [
    '../_base_/models/resnet50.py', '../_base_/datasets/laser_data_cropped.py',
    '../_base_/schedules/imagenet_bs256.py', '../_base_/default_runtime.py'
]

_deprecation_ = dict(
    expected='resnet50_8xb32_in1k.py',
    reference='https://github.com/open-mmlab/mmclassification/pull/508',
)
