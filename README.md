# MVImgNet: A Large-scale Dataset of Multi-view Images
<img src="./assets/teaser_ori.png" width="900"/>

by [Xianggang Yu*](https://larry-u.github.io/), [Mutian Xu*†](https://mutianxu.github.io/), Yidan Zhang*, Haolin Liu*, Chongjie Ye*,
Yushuang Wu, Zizheng Yan, Chenming Zhu, Zhangyang Xiong, Tianyou Liang,
[Guanying Chen](https://guanyingc.github.io/), Shuguang Cui, [Xiaoguang Han‡](https://gaplab.cuhk.edu.cn/) from [GAP-Lab](https://gaplab.cuhk.edu.cn/).


## Introduction
This repository is built for:

**MVImgNet**: A Large-scale Dataset of Multi-view Images **(CVPR2023)** [[arXiv](http://arxiv.org/abs/2303.06042)]


If you find our work useful in your research, please consider citing:
```
@inproceedings{yu2023mvimgnet,
    title     = {MVImgNet: A Large-scale Dataset of Multi-view Images},
    author    = {Yu, Xianggang and Xu, Mutian and Zhang, Yidan and Liu, Haolin and Ye, Chongjie and Wu, Yushuang and Yan, Zizheng and Liang, Tianyou and Chen, Guanying and Cui, Shuguang, and Han, Xiaoguang},
    booktitle = {CVPR},
    year      = {2023}
}
```

## Dataset
MVImgNet contains **6.5 million** frames from **219,188** videos crossing objects from **238** classes. We provide an OneDrive link to download the full data. Please fill out this [form](https://docs.google.com/forms/d/e/1FAIpQLSfU9BkV1hY3r75n5rc37IvlzaK2VFYbdsvohqPGAjb2YWIbUg/viewform?usp=sf_link) to get the download link and password.

We split the full data into 42 zip files, the total size is about 3.4 TB.

### Usage
```
cd path/to/mvimgnet_zip_file
unzip './*.zip'
```

### Folder structure
```
|-- ROOT
    |-- class_label
        |-- instance_id
            |-- images
            |-- sparse/0
                |-- cameras.bin   # COLMAP reconstructed cameras
                |-- images.bin    # binary data of input images
                |-- points3D.bin  # COLMAP reconstructed sparse point cloud (not dense) 
```

The mapping between `class_label` and class name can be found in [mvimgnet_category.txt](https://github.com/GAP-LAB-CUHK-SZ/MVImgNet/blob/main/mvimgnet_category.txt).

The `images` folder contains the multi-view images, and the `sparse` folder contains the reconstructed camera parameters using COLMAP. It is recommended to use the functions provided by [COLMAP](https://github.com/colmap/colmap/blob/dev/scripts/python/read_write_model.py) to read the binary files under `sparse` folder. Moreover, the `gen_poses` function from [this repo](https://github.com/Fyusion/LLFF/tree/master/llff/poses) is recommended to convert the poses for NeRF training.

### Tips for downloading MVImgNet through Ubuntu
We provide tips [at here](https://docs.google.com/document/d/1krVb4B3rZw-0FaBBPS7c3SJKfqq5AVYTs2HN2LnlBPQ/edit?usp=sharing) for downloading our dataset through Ubuntu system (command line style).

### MVPNet
MVPNet now contains 87,825 point clouds from 180 categories. Please fill out the following [form](https://docs.google.com/forms/d/e/1FAIpQLSeZlpezgzmCufD94meHv-Pl_54RpNu2jZqMsyW2GCkVouyomQ/viewform?usp=sf_link) to download MVPNet.

## License

The data is released under the MVImgNet Terms of Use, and the code is released under the Attribution-NonCommercial 4.0 International License.

Copyright (c) 2023

## Acknowledgement

Thanks to [Gege Gao](https://github.com/GGGHSL) for providing tips on downloading our dataset.

