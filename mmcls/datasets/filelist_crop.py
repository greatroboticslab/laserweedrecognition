import os
import glob
import random
import re


if __name__ == '__main__':
    train_name2cls, val_name2cls = {}, {}
    train_list, val_list = [], []
    with open("/data/laserclassification/extracted/croped_split/meta/train.txt", "r") as f:
        for line in f:
            file_name, class_id = line.split(" ")
            file_name = file_name.split("/")[1].split(".")[0]
            train_name2cls[file_name] = class_id
    with open("/data/laserclassification/extracted/croped_split/meta/val.txt", "r") as f:
        for line in f:
            file_name, class_id = line.split(" ")
            file_name = file_name.split("/")[1].split(".")[0]
            val_name2cls[file_name] = class_id
    imgs = os.listdir("/data/laserclassification/extracted/croped_split/")
    for im in imgs:
        name = im.split('.')[0]
        if name in train_name2cls:
            train_list.append(im + " " + train_name2cls[name])
        elif name in val_name2cls:
            val_list.append(im + " " + val_name2cls[name])
        else:
            print(im)
    print("Train=", len(train_list), "**********Val=", len(val_list))

    total_list = train_list + val_list
    list1, list0 = [], []
    for it in total_list:
        if " 1"  in it:
            list1.append(it)
        else:
            list0.append(it)
    print(len(list1), len(list0))

    train_split, val_split = [], []
    for it in list0 + list1:
        if random.random() >= 0.7:
            val_split.append(it)
        else:
            train_split.append(it)
    print(len(train_split), len(val_split))
    with open("train.txt", "w") as f:
        for l in train_split:
            f.write(l)
    with open("val.txt", "w") as f:
        for l in val_split:
            f.write(l)