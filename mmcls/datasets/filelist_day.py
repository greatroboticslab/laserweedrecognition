import os
import glob
import random
import re
from shutil import copyfile
# 生成train.txt和val.txt

#需要改为您自己的路径
root_dir = "/data/laserclassification/extracted/day_split/"
#在该路径下有train,val，meta三个文件夹
train_dir = os.path.join(root_dir, "train")
val_dir = os.path.join(root_dir, "val")
meta_dir = os.path.join(root_dir, "meta")

def generate_txt(images_dir,map_dict):
    # 读取所有文件名
    imgs_dirs = glob.glob(images_dir+"/*/*")
    # 打开写入文件
    typename = images_dir.split("/")[-1]
    target_txt_path = os.path.join(meta_dir,typename+".txt")
    f = open(target_txt_path,"w")
    # 遍历所有图片名
    for img_dir in imgs_dirs:
        # 获取第一级目录名称
        filename = img_dir.split("/")[-2]
        num = map_dict[filename]
        # 写入文件
        relate_name = re.findall(typename+"/([\w / - .]*)",img_dir)
        f.write(relate_name[0]+" "+num+"\n")

def get_map_dict():
    # 读取所有类别映射关系
    class_map_dict = {
    }
    with open(os.path.join(meta_dir,"classmap.txt"),"r") as F:
        lines = F.readlines()
        for line in lines:
            line = line.split("\n")[0]
            filename,cls,num = line.split(" ")
            class_map_dict[filename] = num
    return class_map_dict

if __name__ == '__main__':
    '''
    for it in os.listdir(root_dir):
        if it == 'meta' or it == 'val' or it == 'train':
            continue
        src_folder = os.path.join(root_dir, it)
        for src in os.listdir(src_folder):
            src_path = os.path.join(src_folder, src)
            flag = "val" if random.random() >= 0.7 else "train"
            dst_folder = "/data/laserclassification/extracted/day_split/%s/%s/" % (flag, it)
            dst_path = os.path.join(dst_folder, src)
            copyfile(src_path, dst_path)
    exit(0)
    #'''
    class_map_dict = get_map_dict()
    generate_txt(images_dir=train_dir,map_dict=class_map_dict)
    generate_txt(images_dir=val_dir,map_dict=class_map_dict)
