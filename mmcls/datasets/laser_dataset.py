import numpy as np

from .builder import DATASETS
from .base_dataset import BaseDataset

@DATASETS.register_module()
class LaserDayDataset(BaseDataset):
    CLASSES = ["day1","day2","day3","day4","day5"]#***********************************
    def load_annotations(self):
        assert isinstance(self.ann_file, str)
        data_infos = []
        with open(self.ann_file) as f:
            samples = [x.strip().split(' ') for x in f.readlines()]
            for filename, gt_label in samples:
                info = {'img_prefix': self.data_prefix}
                info['img_info'] = {'filename': filename}
                info['gt_label'] = np.array(gt_label, dtype=np.int64)
                data_infos.append(info)
            return data_infos

@DATASETS.register_module()
class LaserDataset(BaseDataset):
    CLASSES = ["green", "red"]  # ***********************************
    def load_annotations(self):
        assert isinstance(self.ann_file, str)
        data_infos = []
        with open(self.ann_file) as f:
            samples = [x.strip().split(' ') for x in f.readlines()]
            for filename, gt_label in samples:
                info = {'img_prefix': self.data_prefix}
                info['img_info'] = {'filename': filename}
                info['gt_label'] = np.array(gt_label, dtype=np.int64)
                data_infos.append(info)
            return data_infos