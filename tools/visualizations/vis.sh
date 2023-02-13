python vis_cam.py \
    /home/mtsu/workspace/zjx/mmclassification-0.18.0/tools/f1_vis/success/IMG453.jpg \
    /home/mtsu/workspace/zjx/mmclassification-0.18.0/configs/resnet/resnet50_b32x8_imagenet.py \
    /data/laserclassification/classification_split/results/epoch_100.pth \
    --target-layers=model.backbone.layer4.2